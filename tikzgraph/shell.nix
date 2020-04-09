let pkgs = import <nixpkgs> { };
in pkgs.mkShell {
  buildInputs = with pkgs; [
    gnumake
    tectonic
    (python3.withPackages (p: with p; [ networkx ]))
  ];
}
