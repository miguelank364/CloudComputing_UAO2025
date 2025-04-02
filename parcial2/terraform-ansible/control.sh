#!/bin/bash

echo "Iniciando aprovisionamiento de la máquina de control..."

apt-get update

apt-get install -y software-properties-common gnupg2 curl unzip python3 python3-pip sshpass

echo "Instalando Ansible..."
apt-add-repository --yes --update ppa:ansible/ansible
apt-get install -y ansible

echo "Instalando Terraform..."
wget -O- https://apt.releases.hashicorp.com/gpg | gpg --dearmor | tee /usr/share/keyrings/hashicorp-archive-keyring.gpg
echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/hashicorp.list
apt-get update && apt-get install -y terraform

echo "Creando estructura de directorios para el proyecto..."
mkdir -p /home/vagrant/terraform
mkdir -p /home/vagrant/ansible/roles/apache/{tasks,templates}
chown -R vagrant:vagrant /home/vagrant/terraform /home/vagrant/ansible

echo "Generando clave SSH para acceso a la máquina target..."
su - vagrant -c "ssh-keygen -t rsa -N '' -f ~/.ssh/id_rsa"

echo "Creando archivo inventory.ini para Ansible..."
cat > /home/vagrant/ansible/inventory.ini << 'EOL'
[webservers]
web-node ansible_host=192.168.50.2 ansible_user=vagrant ansible_ssh_private_key_file=/home/vagrant/.ssh/id_rsa

[all:vars]
ansible_python_interpreter=/usr/bin/python3
EOL

echo "Creando playbook de Apache para Ansible..."
cat > /home/vagrant/ansible/apache-playbook.yml << 'EOL'
---
- name: Configurar servidor web Apache
  hosts: webservers
  become: yes
  
  tasks:
    - name: Actualizar caché de apt
      apt:
        update_cache: yes
      
    - name: Instalar Apache
      apt:
        name: apache2
        state: present
      
    - name: Asegurar que Apache está en ejecución
      service:
        name: apache2
        state: started
        enabled: yes
      
    - name: Crear página de bienvenida personalizada
      template:
        src: "{{ playbook_dir }}/roles/apache/templates/index.html.j2"
        dest: /var/www/html/index.html
        owner: www-data
        group: www-data
        mode: '0644'
      
    - name: Permitir el tráfico HTTP en el firewall
      ufw:
        rule: allow
        name: Apache
        state: enabled
      ignore_errors: yes
      
    - name: Mostrar URL del servidor web
      debug:
        msg: "El servidor Apache está ejecutándose en http://192.168.50.2"
EOL

echo "Creando plantilla HTML para Apache..."
mkdir -p /home/vagrant/ansible/roles/apache/templates
cat > /home/vagrant/ansible/roles/apache/templates/index.html.j2 << 'EOL'
<!DOCTYPE html>
<html>
<head>
    <title>Bienvenido al Servidor Apache</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 0;
            background-color: #f4f4f4;
            color: #333;
        }
        .container {
            width: 80%;
            margin: auto;
            overflow: hidden;
            padding: 20px;
        }
        header {
            background: #50b3a2;
            color: white;
            padding: 20px;
            text-align: center;
        }
        footer {
            background: #333;
            color: white;
            text-align: center;
            padding: 10px;
            position: fixed;
            bottom: 0;
            width: 100%;
        }
        .logo {
            text-align: center;
            margin: 20px 0;
        }
        .logo img {
            max-width: 200px;
        }
    </style>
</head>
<body>
    <header>
        <h1>Bienvenido al Servidor Apache</h1>
    </header>
    
    <div class="container">
        <div class="logo">
            <img src="https://httpd.apache.org/images/httpd_logo_wide_new.png" alt="Apache HTTP Server Logo">
        </div>
        
        <h2>Configuración completada</h2>
        <p>Este servidor Apache ha sido configurado automáticamente mediante scripts de implementación.</p>
        
        <p>Esta página demuestra que la configuración automatizada fue exitosa. El servidor está funcionando correctamente y listo para alojar tus aplicaciones web.</p>
        
        <h3>Información del servidor</h3>
        <ul>
            <li>Servidor: Apache HTTP Server</li>
            <li>Versión: 2.4.x</li>
            <li>Configuración: Personalizada</li>
        </ul>
    </div>
    
    <footer>
        <p>Página Personalizada de Apache - © 2023</p>
    </footer>
</body>
</html>
EOL

echo "Creando configuración de Terraform..."
cat > /home/vagrant/terraform/main.tf << 'EOL'
# Configuración de proveedores
terraform {
  required_providers {
    null = {
      source = "hashicorp/null"
      version = "~> 3.0"
    }
  }
}

# Recurso para configurar la máquina web-node
resource "null_resource" "web_node" {
  triggers = {
    always_run = "${timestamp()}"
  }

  provisioner "remote-exec" {
    inline = [
      "echo 'Terraform ha conectado exitosamente a la máquina web-node'",
      "echo 'Configuración inicial completada a través de Terraform'"
    ]

    connection {
      type        = "ssh"
      user        = "vagrant"
      private_key = file("~/.ssh/id_rsa")
      host        = "192.168.50.2"
    }
  }

  provisioner "local-exec" {
    command = "cd /home/vagrant/ansible && ansible-playbook -i inventory.ini apache-playbook.yml || echo 'Playbook falló pero continuando...'"
    on_failure = continue
  }
}

output "web_node_status" {
  value = "La configuración de web-node se ha completado correctamente. Apache debe estar funcionando en http://192.168.50.2"
}
EOL

# Ajustar permisos
chown -R vagrant:vagrant /home/vagrant/ansible /home/vagrant/terraform
find /home/vagrant/ansible -type f -exec chmod 644 {} \;
find /home/vagrant/ansible -type d -exec chmod 755 {} \;
chmod 600 /home/vagrant/.ssh/id_rsa

echo "Máquina de control configurada correctamente"