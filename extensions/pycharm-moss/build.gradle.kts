# MOSS v9.3 - PyCharm Plugin Build Configuration

plugins {
    id("org.jetbrains.intellij") version "1.16.0"
    kotlin("jvm") version "1.9.20"
}

group = "com.moss-devtools"
version = "9.3.0"

repositories {
    mavenCentral()
}

intellij {
    version.set("2023.2")
    type.set("PC")  // PyCharm Community
    plugins.set(listOf("PythonCore"))
}

dependencies {
    implementation("com.google.code.gson:gson:2.10.1")
    implementation(kotlin("stdlib-jdk8"))
    testImplementation(kotlin("test"))
    testImplementation("org.junit.jupiter:junit-jupiter:5.10.0")
}

tasks {
    withType<org.jetbrains.kotlin.gradle.tasks.KotlinCompile> {
        kotlinOptions.jvmTarget = "17"
    }

    patchPluginXml {
        sinceBuild.set("232")
        untilBuild.set("241.*")
    }

    signPlugin {
        certificateChain.set(System.getenv("CERTIFICATE_CHAIN"))
        privateKey.set(System.getenv("PRIVATE_KEY"))
        password.set(System.getenv("PRIVATE_KEY_PASSWORD"))
    }

    publishPlugin {
        token.set(System.getenv("PUBLISH_TOKEN"))
    }
}
