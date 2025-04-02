#!/bin/bash
# Script de aprovisionamiento para la máquina target (web-node)

echo "Iniciando aprovisionamiento de la máquina target..."

# Actualizar repositorios
apt-get update

# Instalar dependencias básicas
apt-get install -y openssh-server python3

# Configurar firewall para permitir conexiones SSH
apt-get install -y ufw
ufw allow ssh

echo "Máquina target configurada básicamente"