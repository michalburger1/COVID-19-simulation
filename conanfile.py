from conans import ConanFile, CMake

class COVID19Simulation(ConanFile):
    name = "COVID-19-simulation"
    description = 'Simulating COVID-19 in Slovakia'
    url = "https://github.com/lukipuki/COVID-19-simulation",
    license = 'Unlicense'
    version = "1.0.0"
    settings = "os", "compiler", "build_type", "arch"
    generators = "cmake_paths"
    scm = {
        "type": "git",
        "url": "auto"
    }

    build_requires = "gtest/1.8.1"
    requires = "yaml-cpp/0.6.3"

    def build(self):
        cmake = CMake(self)
        cmake.configure()

        if self.should_build:
            cmake.build()
        if self.should_test:
            cmake.test(output_on_failure=True)

    def package(self):
        cmake = CMake(self)
        cmake.configure()
        # cmake.install()