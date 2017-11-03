#!/bin/sh -x

openqa_host=http://kimball.arch.suse.de
distri=opensuse
version=Tumbleweed
flavor=DVD
arch=x86_64
iso=openSUSE-Tumbleweed-DVD-x86_64-Snapshot20171009-Media.iso
build=20171009
hdd=opensuse-Tumbleweed-x86_64-20171009-textmode@64bit.qcow2

POSITIONAL=()
while [[ $# -gt 0 ]]
do
key="$1"

case $key in
    -h|--host)
    openqa_host="$2"
    shift # past argument
    shift # past value
    ;;
    -v|--version)
    version="$2"
    shift # past argument
    shift # past value
    ;;
    -d|--distri)
    distri="$2"
    shift # past argument
    shift # past value
    ;;
    -f|--flavor)
    flavor="$2"
    shift # past argument
    shift # past value
    ;;
    -a|--arch)
    arch="$2"
    shift # past argument
    shift # past value
    ;;
    -i|--iso)
    iso="$2"
    shift # past argument
    shift # past value
    ;;
    -b|--build)
    build="$2"
    shift # past argument
    shift # past value
    ;;
    --hdd)
    hdd="$2"
    shift # past argument
    shift # past value
    ;;
esac
done
set -- "${POSITIONAL[@]}" # restore positional parameters

/usr/bin/openqa-client --host $openqa_host  isos post DISTRI=$distri VERSION=$version FLAVOR=$flavor ARCH=$arch ISO=$iso BUILD=$build HDD_1=$hdd
