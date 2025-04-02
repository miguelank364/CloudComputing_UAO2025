// Correlation Matrix Visualization using D3.js

document.addEventListener('DOMContentLoaded', function() {
  // Load data when button is clicked
  document.getElementById('loadCorrelationBtn').addEventListener('click', loadCorrelationData);

  function loadCorrelationData() {
    // Show loading message
    const matrixContainer = document.getElementById('correlation-matrix');
    matrixContainer.innerHTML = '<p>Cargando datos, por favor espere...</p>';

    // Load CSV data
    d3.csv('optical_network.csv', function(d) {
      // Parse numeric values
      return {
        'Node Number': +d['Node Number'],
        'Thread Number': +d['Thread Number'],
        'Spatial Distribution': d['Spatial Distribution'],
        'Temporal Distribution': d['Temporal Distribution'],
        'T/R': parseFloat(d['T/R'].replace(',', '.')), // Handle comma as decimal separator
        'Processor Utilization': parseFloat(d['Processor Utilization '].replace(',', '.')),
        'Channel Waiting Time': parseFloat(d['Channel Waiting Time'].replace(',', '.')),
        'Input Waiting Time': parseFloat(d['Input Waiting Time'].replace(',', '.')),
        'Network Response Time': parseFloat(d['Network Response Time'].replace(',', '.')),
        'Channel Utilization': parseFloat(d['Channel Utilization'].replace(',', '.'))
      };
    }).then(function(data) {
      // Create the correlation matrix
      createCorrelationMatrix(data);
    }).catch(function(error) {
      console.error('Error loading data:', error);
      matrixContainer.innerHTML = '<p>Error cargando datos. Intente de nuevo.</p>';
    });
  }

  function createCorrelationMatrix(data) {
    // Clear previous content
    const matrixContainer = document.getElementById('correlation-matrix');
    matrixContainer.innerHTML = '';

    // Get numeric columns for the matrix (excluding categorical variables)
    const numericColumns = ['Node Number', 'Thread Number', 'T/R', 
                           'Processor Utilization', 'Channel Waiting Time', 
                           'Input Waiting Time', 'Network Response Time', 
                           'Channel Utilization'];
    
    // Define dimensions
    const padding = 28;
    const size = 150;
    const width = size * numericColumns.length + padding * (numericColumns.length + 1);
    const height = width;

    // Create SVG
    const svg = d3.create('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [-padding, 0, width, height]);

    // Define scales
    const x = numericColumns.map(col => 
      d3.scaleLinear()
        .domain(d3.extent(data, d => d[col]))
        .rangeRound([padding / 2, size - padding / 2])
    );

    const y = x.map(x => x.copy().range([size - padding / 2, padding / 2]));

    // Color scale based on Spatial Distribution
    const color = d3.scaleOrdinal()
      .domain(['UN', 'HR', 'BR', 'PS'])
      .range(d3.schemeCategory10);

    // Add axis
    const axisx = d3.axisBottom()
      .ticks(6)
      .tickSize(size * numericColumns.length);
      
    svg.append('g')
      .selectAll('g')
      .data(x)
      .join('g')
      .attr('transform', (d, i) => `translate(${i * size},0)`)
      .each(function(d, i) {
        return d3.select(this).call(axisx.scale(d));
      })
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('.tick line').attr('stroke', '#ddd'));

    const axisy = d3.axisLeft()
      .ticks(6)
      .tickSize(-size * numericColumns.length);
      
    svg.append('g')
      .selectAll('g')
      .data(y)
      .join('g')
      .attr('transform', (d, i) => `translate(0,${i * size})`)
      .each(function(d, i) {
        return d3.select(this).call(axisy.scale(d));
      })
      .call(g => g.select('.domain').remove())
      .call(g => g.selectAll('.tick line').attr('stroke', '#ddd'));

    // Add style for hidden circles
    svg.append('style')
      .text(`
        circle.hidden { 
          fill: #000; 
          fill-opacity: 1; 
          r: 1px; 
        }
        circle {
          transition: r 0.2s;
        }
      `);

    // Create cells for each combination of variables
    const cell = svg.append('g')
      .selectAll('g')
      .data(d3.cross(d3.range(numericColumns.length), d3.range(numericColumns.length)))
      .join('g')
      .attr('transform', ([i, j]) => `translate(${i * size},${j * size})`);

    cell.append('rect')
      .attr('fill', 'none')
      .attr('stroke', '#aaa')
      .attr('x', padding / 2 + 0.5)
      .attr('y', padding / 2 + 0.5)
      .attr('width', size - padding)
      .attr('height', size - padding);

    // Add circles for each data point
    cell.each(function([i, j]) {
      d3.select(this).selectAll('circle')
        .data(data.filter(d => !isNaN(d[numericColumns[i]]) && !isNaN(d[numericColumns[j]])))
        .join('circle')
        .attr('cx', d => x[i](d[numericColumns[i]]))
        .attr('cy', d => y[j](d[numericColumns[j]]));
    });

    const circle = cell.selectAll('circle')
      .attr('r', 3.5)
      .attr('fill-opacity', 0.7)
      .attr('fill', d => color(d['Spatial Distribution']));

    // Add column labels
    svg.append('g')
      .style('font', 'bold 10px sans-serif')
      .style('pointer-events', 'none')
      .selectAll('text')
      .data(numericColumns)
      .join('text')
      .attr('transform', (d, i) => `translate(${i * size},0)`)
      .attr('x', padding)
      .attr('y', padding - 10)
      .attr('text-anchor', 'start')
      .attr('fill', '#000')
      .text(d => d);

    // Add brush functionality
    const brush = d3.brush()
      .extent([[padding / 2, padding / 2], [size - padding / 2, size - padding / 2]])
      .on('start', brushStarted)
      .on('brush', brushed)
      .on('end', brushEnded);

    cell.call(brush);

    let brushCell;

    function brushStarted() {
      if (brushCell !== this) {
        d3.select(brushCell).call(brush.move, null);
        brushCell = this;
      }
    }

    function brushed(event, [i, j]) {
      const selection = event.selection;
      let selected = [];
      
      if (selection) {
        const [[x0, y0], [x1, y1]] = selection;
        
        // Update visibility of circles
        circle.classed('hidden', d => {
          const outOfBrush = x0 > x[i](d[numericColumns[i]]) || 
                            x1 < x[i](d[numericColumns[i]]) || 
                            y0 > y[j](d[numericColumns[j]]) || 
                            y1 < y[j](d[numericColumns[j]]);
          
          if (!outOfBrush) {
            selected.push(d);
          }
          
          return outOfBrush;
        });
        
        // Highlight selected circles across all cells
        if (selected.length > 0) {
          circle.attr('r', d => selected.includes(d) ? 6 : 3.5)
                .attr('stroke', d => selected.includes(d) ? '#000' : null)
                .attr('stroke-width', d => selected.includes(d) ? 1 : 0);
                
          // Display info about selected points
          const selectedInfo = document.getElementById('selected-point-info');
          const pointDetails = document.getElementById('point-details');
          
          selectedInfo.classList.remove('hidden');
          pointDetails.textContent = `${selected.length} puntos seleccionados`;
          
          if (selected.length === 1) {
            const point = selected[0];
            let detailText = `Node: ${point['Node Number']}, Thread: ${point['Thread Number']}, `;
            detailText += `T/R: ${point['T/R']}, Resp Time: ${point['Network Response Time'].toFixed(2)}`;
            pointDetails.textContent = detailText;
          }
        }
      }
    }

    function brushEnded(event) {
      if (!event.selection) {
        circle.classed('hidden', false)
              .attr('r', 3.5)
              .attr('stroke', null);
              
        document.getElementById('selected-point-info').classList.add('hidden');
      }
    }

    // Add legend for colors
    const legend = svg.append('g')
      .attr('transform', `translate(${width - 120}, 10)`);

    legend.selectAll('rect')
      .data(['UN', 'HR', 'BR', 'PS'])
      .join('rect')
      .attr('y', (d, i) => i * 20)
      .attr('width', 12)
      .attr('height', 12)
      .attr('fill', d => color(d));

    legend.selectAll('text')
      .data(['UN', 'HR', 'BR', 'PS'])
      .join('text')
      .attr('x', 20)
      .attr('y', (d, i) => i * 20 + 10)
      .attr('font-size', '10px')
      .attr('text-anchor', 'start')
      .attr('dominant-baseline', 'middle')
      .text(d => d);

    // Append the SVG to the container
    matrixContainer.appendChild(svg.node());
  }
});
