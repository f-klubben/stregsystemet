{ callPackage, lib, python3Packages }: let
    # Based on requirements.txt, determine dependencies to fetch from nixpkgs
    requirements = ../requirements.txt;
    # Read file and split it into lines
    lines = lib.lists.remove "" (lib.strings.splitString "\n" (builtins.readFile requirements));
    packages = map (pkg: builtins.elemAt (lib.strings.splitString "==" pkg) 0) lines;
    filteredPackages = builtins.filter (pkg: pkg != "Django-Select2") packages;
    
    django-select2 = callPackage ./django-select2.nix { };
in

[django-select2] ++ map (pkg: python3Packages.${lib.toLower pkg}) filteredPackages
