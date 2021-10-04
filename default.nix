{ pkgs ? import <nixpkgs> {}
, python ? pkgs.python39
, toLower ? pkgs.lib.toLower
}:
let
	reqs = builtins.readFile ./requirements.txt;
	# We split the lines
	split = builtins.split "\n" reqs;
	# We remove empty lists and null values
	lines = builtins.filter (x: builtins.isString x && x != "") split;
	# Now we have tuples on the form [ name version ]
	reqtuples = builtins.map (builtins.match "(.*)==(.*)") lines;
in
pkgs.stdenv.mkDerivation rec {
    name = "stregsystemet";
    src = ./.;

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
			else throw "${name} doesn't exist in pythonPackages"
		) requirements
	);

    buildInputs = [
        pythonWithDeps
    ];
}
