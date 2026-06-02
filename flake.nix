{
  description = "FancyQR - Styled SVG QR Code Generator and Link Shortener running on Cloudflare Workers";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
      in
      {
        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.nodejs_22
            pkgs.nodePackages.typescript-language-server
          ];
          
          shellHook = ''
            echo "⚡ Welcome to the FancyQR Cloudflare Worker development environment! ⚡"
            echo "Node.js version: $(${pkgs.nodejs_22}/bin/node --version)"
            echo "Commands available:"
            echo "  npm install      - Install project dependencies"
            echo "  npm run dev      - Start the local Wrangler development server"
            echo "  npm run deploy   - Deploy your worker to Cloudflare"
          '';
        };
      }
    );
}
