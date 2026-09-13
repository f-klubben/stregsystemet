{
    description = "F-klubbens Stregsystem";

    # define nixpkgs version to use
    inputs = {
        nixpkgs.url = "nixpkgs/nixos-25.11";
    };

    outputs = { self, nixpkgs }: let 
        system = "x86_64-linux";
        pkgs = import nixpkgs { inherit system; };
    in {
        # Define the shell, here we're just setting the packages required for the devshell
        devShells.${system}.default = self.packages.${system}.default.shell;

        # Default package for the stregsystem
        packages.${system} = {
            default = pkgs.callPackage ./nix-support { };

            # Test VM
            vm = (nixpkgs.lib.nixosSystem {
                inherit system;
                modules = [
                    self.nixosModules.default
                    {
                        users.users.root.password = "root";
                        networking.hostName = "fklub";
                        system.stateVersion = "25.11";
                        stregsystemet = {
                            enable = true;
                            port = 80;
                            testData = {
                                enable = true;
                            };
                        };
                    }
                ];
            }).config.system.build.vm;
        };

        # NixOS system modules
        nixosModules.default = import ./nix-support/module.nix;
    };
}
