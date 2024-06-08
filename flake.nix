{
    description = "F-klubbens Stregsystem";

    # define nixpkgs version to use
    inputs = {
        nixpkgs.url = "nixpkgs/nixos-23.11";
    };

    outputs = { self, nixpkgs }: let 
        system = "x86_64-linux";
        pkgs = import nixpkgs { inherit system; };

        # Custom package as django-select2 is not in nixpkgs
        django-select2 = pkgVersion: pkgs.python311Packages.buildPythonPackage rec {
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
        };

        # Based on requirements.txt, determine dependencies to fetch from nixpkgs
        requirements = ./requirements.txt;
        # Read file and split it into lines
        lines = pkgs.lib.lists.remove "" (pkgs.lib.strings.splitString "\n" (builtins.readFile requirements));
        
        # Map a function to convert the list of strings into a list of derivations
        dependencies = ver: builtins.map 
            (package: let 
                # pkgList is a function defined here via currying, it will just return the item at index in the list generated after splitting by ==
                pkgList = builtins.elemAt (pkgs.lib.strings.splitString "==" package);
                pkgName = pkgs.lib.strings.toLower (pkgList 0); 
                pkgVersion = pkgList 1;
            # Instead of fetching from nixpkgs, evaluate a custom version of django-select2
            in if pkgName == "django-select2" then
                django-select2 pkgVersion
            else
                # Add the standard derivation of the package, attempt to set the version
                ver."${pkgName}".overrideAttrs { version = pkgVersion; }
            )
            lines;

    in {
        # Define the shell, here we're just setting the packages required for the devshell
        devShells.${system}.default = pkgs.mkShell {
            packages = (dependencies pkgs.python3Packages) ++ [pkgs.mailhog pkgs.black];
        };
        shellHook = ''
            export PS1="(FIT) $PS1"
        ''

        # Default package for the stregsystem
        packages.${system}.default = let
            env = pkgs.python3.withPackages (_: []);
        in pkgs.stdenv.mkDerivation {
            pname = "Stregsystemet";
            version = "latest";
            src = ./.;

	          installPhase = ''
		            mkdir -p $out/bin
		            mkdir -p $out/share/stregsystemet

                cp local.cfg.skel local.cfg
                echo "${env.interpreter} $out/share/stregsystemet/manage.py \$@" > $out/bin/stregsystemet
                sed -i '1 i #!${pkgs.bash}/bin/bash' $out/bin/stregsystemet
                chmod +x $out/bin/stregsystemet

                sed -i '1d' manage.py

		            cp ./* $out/share/stregsystemet -r
	          '';
        };
    };
}
