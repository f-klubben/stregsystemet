{pkgs, py}:

py.buildPythonPackage {
    pname = "Django-Select2";
    version = "5.11.1";
    src = pkgs.fetchurl {
        url = "https://files.pythonhosted.org/packages/a9/67/4a511634562a3108261d6497bd2d6e40af957b9d3d75f30ec95cc68ccf0b/Django-Select2-5.11.1.tar.gz";
        sha256 = "06gb79wikwcwbsny6dz9vp8qv66k0ri8xfd0h3hay58rc7mkrg2a";
    };
    format = "setuptools";
    doCheck = false;
    buildInputs = [];
    checkInputs = [];
    nativeBuildInputs = [];
    propagatedBuildInputs = [
        (py.django-appconf)
    ];
}

