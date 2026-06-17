{ python3Packages, writeText, callPackage, mkShell, mailhog, black }:

let
    projectFile = builtins.fromTOML (builtins.readFile ../pyproject.toml);
    pname = projectFile.project.name;
    version = projectFile.project.version;
    src = ../.;
    dependencies = callPackage ./dependencies.nix { };
    pyprojectAddition = writeText "pyproject-addition.toml" ''
        [project.scripts]
        ${pname} = "treo.manage:main"
    '';
in

python3Packages.buildPythonApplication {
    inherit pname version src;
    propagatedBuildInputs = dependencies;
    pyproject = true;
    build-system = [ python3Packages.setuptools ];
    # prepare
    preBuild = ''
        sed -i 's/^import setup_utils$/from . import setup_utils/' manage.py
        cp manage.py treo
        cp setup_utils.py treo
        cat ${pyprojectAddition} >> pyproject.toml
    '';

    passthru.shell = mkShell {
        packages = dependencies ++ [mailhog black];
    };
}
