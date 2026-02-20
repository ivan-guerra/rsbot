{ pkgs ? import <nixpkgs> {} }:

pkgs.mkShell {
  buildInputs = with pkgs; [
    # Rust toolchain
    cargo
    rustc
    rustfmt
    clippy
    
    # Required system libraries for dependencies
    xorg.libX11
    xorg.libXi
    xorg.libXtst
    xorg.libXrandr
    xdotool
    
    # Optional but useful
    pkg-config
  ];

  # Set library path for runtime
  LD_LIBRARY_PATH = pkgs.lib.makeLibraryPath [
    pkgs.xorg.libX11
    pkgs.xorg.libXi
    pkgs.xorg.libXtst
    pkgs.xorg.libXrandr
  ];

  shellHook = ''
    echo "rsbot development environment loaded"
  '';
}
