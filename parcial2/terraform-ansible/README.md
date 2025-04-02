# Terraform & Ansible Infrastructure Automation

Este proyecto demuestra la automatización de infraestructura utilizando Vagrant, Terraform y Ansible para configurar un servidor web Apache en un entorno virtualizado de dos nodos.

## Arquitectura

El proyecto implementa una arquitectura de dos máquinas virtuales:

- **Control Node (192.168.50.3)**: Máquina que tiene instalado Terraform y Ansible, actuando como orquestador para la configuración de infraestructura.
- **Web Node (192.168.50.2)**: Máquina objetivo donde se despliega un servidor web Apache.

## Prerrequisitos

- [VirtualBox](https://www.virtualbox.org/wiki/Downloads) (6.1 o superior)
- [Vagrant](https://www.vagrantup.com/downloads) (2.2.0 o superior)


## Instalación

1. Clone este repositorio:
   ```bash
   git clone <url-del-repositorio>
   cd CloudComputing_UAO2025/parcial2/terraform-ansible
   ```

2. Inicie las máquinas virtuales con Vagrant:
   ```bash
   vagrant up
   ```
   Este comando creará y configurará ambas máquinas virtuales automáticamente.

## Uso

Una vez que las máquinas estén funcionando:

1. Acceda al nodo de control:
   ```bash
   vagrant ssh control-node
   ```

2. Ejecute el plan de Terraform:
   ```bash
   cd ~/terraform
   terraform init
   terraform apply -auto-approve
   ```

3. Este comando ejecutará automáticamente:
   - Verificación de conectividad SSH con web-node
   - Ejecución del playbook de Ansible que configura Apache

4. Acceda al servidor web en su navegador:
   ```
   http://192.168.50.2
   ```

## Componentes del Proyecto

### Vagrantfile
Define la configuración de ambas máquinas virtuales, establece la red privada, y ejecuta los scripts de aprovisionamiento.

### control.sh
Script de aprovisionamiento para el nodo de control que:
- Instala Ansible y Terraform
- Configura SSH para acceso sin contraseña al nodo web
- Crea directorios y archivos necesarios para Ansible y Terraform
- Prepara un playbook de Ansible para instalar y configurar Apache
- Configura los archivos de Terraform para orquestar la implementación

### web.sh
Script de aprovisionamiento para el nodo web que:
- Actualiza los repositorios del sistema
- Instala SSH y Python (requerido por Ansible)
- Configura el firewall para permitir conexiones SSH

### Ansible
- **inventory.ini**: Define el inventario de servidores para Ansible
- **apache-playbook.yml**: Playbook que instala y configura Apache
- **Templates**: Contiene una página HTML personalizada para Apache

### Terraform
- **main.tf**: Define la configuración de Terraform para establecer conexión con web-node y ejecutar Ansible

## Solución de Problemas

- Si la conexión SSH falla, puede reiniciar el aprovisionamiento:
  ```bash
  vagrant provision
  ```

- Para forzar la reconstrucción completa del entorno:
  ```bash
  vagrant destroy -f
  vagrant up
  ```

## Contribución

Este proyecto fue desarrollado como parte del curso de Cloud Computing en la Universidad Autónoma de Occidente (2025).