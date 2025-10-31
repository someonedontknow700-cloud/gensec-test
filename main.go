package main

import (
    "fmt"
    "os/exec"
)

func main() {
    userInput := "ls; rm -rf /" // Malicious user input that injects an additional command
    cmd := exec.Command("sh", "-c", userInput)

    output, err := cmd.CombinedOutput()
    if err != nil {
        fmt.Println("Error executing command:", err)
        return
    }

    fmt.Println(string(output))
}
