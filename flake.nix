{
  description = "FancyQR - Styled SVG QR Code Generator";

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
          buildInputs = with pkgs; [
            pixi
          ];
        };

        packages.default = pkgs.writeShellScriptBin "fancyqr-web" ''
          exec ${pkgs.pixi}/bin/pixi run --manifest-path ${self}/pixi.toml web
        '';
      }
    ) // {
      nixosModules.default = { config, lib, pkgs, ... }:
        let
          cfg = config.services.fancyqr;
        in
        {
          options.services.fancyqr = {
            enable = lib.mkEnableOption "FancyQR service";
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
              description = "Directory to store app files (including logo.svg).";
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
                # If using a socket, ensure the runtime directory exists
                RuntimeDirectory = if cfg.socket != null then "fancyqr" else null;
                ExecStartPre = pkgs.writeShellScript "fancyqr-setup" ''
                  # Copy the app files and pixi.toml to the data directory if they don't exist
                  mkdir -p ${cfg.dataDir}
                  cp -rn ${self}/* ${cfg.dataDir}/
                  chmod -R u+w ${cfg.dataDir}/
                '';
                ExecStart = let
                  listenArgs = if cfg.socket != null 
                    then "--uds ${cfg.socket}" 
                    else "--host ${cfg.host} --port ${toString cfg.port}";
                in "${pkgs.pixi}/bin/pixi run --manifest-path ${cfg.dataDir}/pixi.toml uvicorn app:app ${listenArgs}";
                Restart = "always";
              };
            };
          };
        };
    };
}
