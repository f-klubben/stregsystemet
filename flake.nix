{
    description = "F-klubbens Stregsystem";

    # define nixpkgs version to use
    inputs = {
        nixpkgs.url = "nixpkgs/nixos-24.05";
    };

    outputs = { self, nixpkgs }: let 
        system = "x86_64-linux";
        pkgs = import nixpkgs { inherit system; };

        dependencies = import ./nix-support { inherit pkgs; };

    in {
        # Define the shell, here we're just setting the packages required for the devshell
        devShells.${system}.default = pkgs.mkShell {
            packages = (dependencies pkgs.python3Packages) ++ [pkgs.mailhog pkgs.black];
        };

        # Default package for the stregsystem
        packages.${system}.default = let
            env = pkgs.python311.withPackages dependencies;
        in pkgs.stdenv.mkDerivation {
            pname = "stregsystemet";
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
