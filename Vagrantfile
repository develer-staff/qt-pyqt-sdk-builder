# -*- coding: utf-8 -*-
# -*- mode: ruby -*-
# vi: set ft=ruby :


# Vagrantfile API/syntax version. Don't touch unless you know what you're doing!
VAGRANTFILE_API_VERSION = "2"


PROVISION_WINDOWS = <<EOF
Import-Module ServerManager
Add-WindowsFeature -Name Net-Framework-Core

(New-Object System.Net.WebClient).DownloadFile("http://go.just-install.it", "$env:WinDir\\just-install.exe")

# We can run only stuff which doesn't show an _interactive_ GUI here.

just-install notepad++
just-install rapidee

just-install python27
just-install python27-pip
EOF


Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
    config.vm.provider "virtualbox" do |v|
        v.gui = true
        v.memory = 4096
    end

    config.vm.provider "vmware_fusion" do |v|
        v.gui = true
        v.vmx["memsize"] = "4096"
    end

    #
    # Windows Server 2008r2 (64-bit)
    #

    config.vm.define "windows" do |config|
        config.vm.box = "lvillani/win2008r2-web"
        config.vm.provision "shell", inline: PROVISION_WINDOWS
    end
end
