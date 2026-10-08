pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}
dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {
        google()
        mavenCentral()
    }
}
rootProject.name = "a2ui-analyser"
include(":app")

// The atomic-catalog library (module :a2ui-atoms) lives one directory up (android/).
// A composite build uses its source directly, so the viewer always runs the library
// as it is in that working tree.
includeBuild("..") {
    dependencySubstitution {
        substitute(module("ai.a2uicatalog:atomic-catalog")).using(project(":a2ui-atoms"))
    }
}
