{ pkgs ? import <nixpkgs> {}
, toLower ? pkgs.lib.toLower
, python ? pkgs.python39
, pythonPackages ? pkgs.python39Packages
}:
let
	customPackages = {
    	django-select2 = import ./django-select2.nix { inherit pkgs pythonPackages; };
    	django-debug-toolbar = import ./django-debug-toolbar.nix { inherit pkgs pythonPackages; };
	};
	reqs = builtins.readFile ./requirements.txt;
	# We split the lines
	split = builtins.split "\n" reqs;
	# We remove empty lists and null values
	lines = builtins.filter (x: builtins.isString x && x != "") split;
	# Now we have tuples on the form [ name version ]
	reqtuples = builtins.map (builtins.match "(.*)==(.*)") lines;
in
pkgs.mkShell rec {
    name = "stregsystemet";

	# This makes the name lowercase
	requirements = builtins.map (builtins.map toLower) reqtuples;
	# We create a python that has our dependencies
	# Here we assume the requirements have the same exact
	# names in pypi and nixpkgs
	pythonWithDeps = python.withPackages (pypkgs:
		builtins.map (x:
			let
				name = builtins.head x;
			in
			if builtins.hasAttr name pypkgs
			then pypkgs.${name}
			else
    			if builtins.hasAttr name customPackages
    			then customPackages.${name}
    			else throw "${name} doesn't exist in pythonPackages"
		) requirements
	);

    buildInputs = [
        pythonWithDeps
    ];
}
