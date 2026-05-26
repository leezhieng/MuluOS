cmake_minimum_required(VERSION 3.20)
project(muluos-kio-bundle VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_AUTOMOC ON)

# Plasma 6 / KF6
find_package(ECM REQUIRED NO_MODULE)
set(CMAKE_MODULE_PATH ${ECM_MODULE_PATH})
include(KDEInstallDirs)
include(KDECMakeSettings)
include(KDECompilerSettings NO_POLICY_SCOPE)
include(ECMQtDeclareLoggingCategory)

find_package(Qt6 REQUIRED COMPONENTS Core)
find_package(KF6 REQUIRED COMPONENTS KIO)

add_library(muluosbundle MODULE
    src/muluosbundleworker.cpp
)

target_link_libraries(muluosbundle PRIVATE
    Qt6::Core
    KF6::KIOCore
)

# KIO 6 workers are loaded as plugins from the kf6/kio directory.
install(TARGETS muluosbundle
    DESTINATION ${KDE_INSTALL_PLUGINDIR}/kf6/kio
)

install(FILES muluosbundle.protocol
    DESTINATION ${KDE_INSTALL_KSERVICESDIR}
)
