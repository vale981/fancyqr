{
  description = "FancyQR - Styled SVG QR Code Generator";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = { self, nixpkgs, flake-utils, uv2nix, pyproject-nix, pyproject-build-systems, ... }:
    let
      inherit (nixpkgs) lib;
    in
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};

        # 1. Load the uv workspace
        workspace = uv2nix.lib.workspace.loadWorkspace {
          workspaceRoot = ./.;
        };

        # 2. Create the Python package set with overlays
        python = pkgs.python313;
        pythonSet = (pkgs.callPackage pyproject-nix.build.packages {
          inherit python;
        }).overrideScope (
          lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            (workspace.mkPyprojectOverlay {
              sourcePreference = "wheel";
            })
          ]
        );

        # 3. Build the virtual environment (the "package")
        # This includes our local project (fancyqr) because it's in the workspace
        fancyqr-env = pythonSet.mkVirtualEnv "fancyqr-env" workspace.deps.default;

      in
      {
        packages.default = fancyqr-env;

        devShells.default = pkgs.mkShell {
          packages = [
            pkgs.uv
            fancyqr-env
          ];
        };
      }
    ) // {
      nixosModules.default = { config, lib, pkgs, ... }:
        let
          cfg = config.services.fancyqr;
        in
        {
          options.services.fancyqr = {
            enable = lib.mkEnableOption "FancyQR service";
            package = lib.mkOption {
              type = lib.types.package;
              default = self.packages.${pkgs.system}.default;
              description = "The package to use for the service.";
            };
            port = lib.mkOption {
              type = lib.types.port;
              default = 8000;
              description = "Port to listen on.";
            };
            host = lib.mkOption {
              type = lib.types.str;
              default = "0.0.0.0";
              description = "Host to bind to.";
            };
            socket = lib.mkOption {
              type = lib.types.nullOr lib.types.path;
              default = null;
              description = "Path to a Unix socket to listen on. If set, host and port are ignored.";
            };
            user = lib.mkOption {
              type = lib.types.str;
              default = "fancyqr";
              description = "User to run the service as.";
            };
            group = lib.mkOption {
              type = lib.types.str;
              default = "fancyqr";
              description = "Group to run the service as.";
            };
            dataDir = lib.mkOption {
              type = lib.types.path;
              default = "/var/lib/fancyqr";
              description = "Directory to store app files (like logo.svg).";
            };
            passwordFile = lib.mkOption {
              type = lib.types.nullOr lib.types.path;
              default = null;
              description = "Path to a file containing the password for link shortening.";
            };
          };

          config = lib.mkIf cfg.enable {
            users.users.${cfg.user} = {
              isSystemUser = true;
              group = cfg.group;
              home = cfg.dataDir;
              createHome = true;
            };
            users.groups.${cfg.group} = { };

            systemd.services.fancyqr = {
              description = "FancyQR Web Service";
              after = [ "network.target" ];
              wantedBy = [ "multi-user.target" ];

              serviceConfig = {
                User = cfg.user;
                Group = cfg.group;
                WorkingDirectory = cfg.dataDir;
                # RuntimeDirectory manages /run/fancyqr automatically
                RuntimeDirectory = if cfg.socket != null then "fancyqr" else null;

                Environment = [
                  "FANCYQR_DB_PATH=${cfg.dataDir}/links.db"
                ];

                # Load password from file if provided
                ExecStartPre = lib.optional (cfg.passwordFile != null) (
                  pkgs.writeShellScript "fancyqr-setup" ''
                    if [ -f "${cfg.passwordFile}" ]; then
                      echo "FANCYQR_PASSWORD=$(cat "${cfg.passwordFile}")" > /run/fancyqr/env
                    fi
                  ''
                );

                EnvironmentFile = lib.optional (cfg.passwordFile != null) "/run/fancyqr/env";
                
                # ExecStart uses the binary from the uv2nix virtualenv
                ExecStart = let
                  listenArgs = if cfg.socket != null 
                    then "--uds ${cfg.socket}" 
                    else "--host ${cfg.host} --port ${toString cfg.port}";
                in "${cfg.package}/bin/fancyqr-web ${listenArgs}";
                
                Restart = "always";
              };
            };
          };
        };
    };
}
