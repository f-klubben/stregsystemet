{
    description = "F-klubbens Stregsystem";

    inputs = {
        nixpkgs.url = "nixpkgs/nixos-unstable";
    };

    outputs = { self, nixpkgs }: let 
        system = "x86_64-linux";
        pkgs = import nixpkgs { inherit system; };
        dependencies = builtins.map 
            (package: let 
                pkgName = pkgs.lib.strings.toLower (builtins.elemAt (pkgs.lib.strings.splitString "==" package) 0); 
                pkgVersion = builtins.elemAt (pkgs.lib.strings.splitString "==" package) 1;
            in if pkgName == "django-select2" then
                pkgs.python311Packages.buildPythonPackage rec {
                    pname = "django_select2";
                    name = "django_select2";
                    version = pkgVersion;
                    src = pkgs.fetchPypi {
                        inherit pname version;
                        sha256 = "sha256-9EaF7hw5CQqt4B4+vCVnAvBWIPPHijwmhECtmmYHCHY=";
                    };
                    format = "pyproject";
                    doCheck = false;
                    propagatedBuildInputs = [pkgs.python311Packages.flit-scm pkgs.python311Packages.django-appconf];
                }
            else
                pkgs.python311Packages."${pkgName}".overrideAttrs { version = pkgVersion;}
            )
            (pkgs.lib.lists.remove "" (pkgs.lib.strings.splitString "\n" (builtins.readFile ./requirements.txt)));

    in {
        devShells.x86_64-linux.default = pkgs.mkShell {
            packages = dependencies;
        };
    };
}
