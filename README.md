# MuluOS

MuluOS is an open-source Linux-based operating system built on top of Debian Linux. It uses Debian's stable, well-tested foundation as a base to assemble a fully customized system and architecture tailored to MuluOS's design goals.

The project is currently in an experimental stage and is primarily focused on the desktop experience. Although a CLI version can also be installed for servers or IoT applications, package availability and stability are not yet guaranteed.

MuluOS Desktop promotes an application model where software is installed through dedicated installers instead of traditional package managers. Our philosophy is that applications should be self-contained, bundling their own dependencies rather than relying heavily on centralized shared libraries, except for essential system and OS-level components.

At the moment, MuluOS is powered by a Python-based build system that scaffolds a minimal Linux environment into a bootable ISO while also generating a modern-looking installer. In the future, we plan to introduce additional custom software for desktop management, application installation, and overall system administration.

Stay tuned for more updates as the project evolves.

## Creator

Lee Zhi Eng

## License

GPL-3.0

