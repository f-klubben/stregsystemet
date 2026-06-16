{ python3Packages, fetchurl }:

let
    pname = "django_select2";
    version = "8.1.2";
    name = "${pname}-${version}";
    url = "https://files.pythonhosted.org/packages/7f/af/2fc371e1dea6686b588ab9cd445e55b63248a525f8c90550767a42dd77bb/${name}.tar.gz";
    sha256 = "sha256-9EaF7hw5CQqt4B4+vCVnAvBWIPPHijwmhECtmmYHCHY=";
    src = fetchurl { inherit url sha256; };
in

python3Packages.buildPythonPackage {
    inherit pname version src;
    format = "pyproject";
    doCheck = false;
    buildInputs = [];
    checkInputs = [];
    nativeBuildInputs = [];
    propagatedBuildInputs = with python3Packages; [
        django-appconf
        flit-scm
    ];
}

