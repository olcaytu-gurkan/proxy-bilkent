import sys
import socket

def main():
    # Port number is required.
    if (len(sys.argv) < 2):
        print("Error! You should provide a port number.")
        exit()

    HOST = "localhost"
    PORT = int(sys.argv[1])

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, PORT))
        s.listen()
        while True:
            conn, address = s.accept()
            # Receive the directed request.
            data = conn.recv(1024)
            decoded_data = ""

            # This is necessary for the data that cannot be decoded (Firefox send those sometimes).
            try:
                decoded_data = data.decode()
            except UnicodeDecodeError:
                continue

            # This means unusual request, probably from Firefox.
            if len(decoded_data.split('\n')) < 2:
                continue

            # Server that we will send the request is parsed. 
            resp_host = decoded_data.split('\n')[1].split(' ')[1]
            # This allows us to ignore other servers.
            if resp_host[:-1] != "www.cs.bilkent.edu.tr":
                continue

            print("Retrieved request from Firefox:")
            print(decoded_data)  # utf_8 encoding is used (default) to present a nicer output like Netcat's.

            file_name = getfilename(decoded_data)
            print("Downloading file: " + file_name)

            # Creating the socket that we will redirect the original request.
            resp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            resp_socket.settimeout(10) # Socket time outs after 10 sec.
            resp_socket.connect((resp_host[:-1], 80))
            resp_socket.sendall(data)
            
            # Receive the first response.
            response = resp_socket.recv(4096)
            response_code = getresponsecode(response)
            if response_code != '200':
                print("Error! File to be downloaded not found. Response code: " + response_code)
                continue
            print("Retrieved: 200 OK")
            print("Saving file..")

            # File content is at the end of the first received response, so parse it.
            file_content = response.decode().split('\r')[-1].lstrip()
            file = open(file_name, "w") # File is first opened in write mode to overwrite anything existed before.
            file.write(file_content)
            file.close()
            # Getting the rest of the response because file can be big.
            while (len(response) > 0):
                # This is opened in append mode because we do not want to overwrite previous data.
                file = open(file_name, "a")
                response = resp_socket.recv(4096)
                file.write(response.decode())
            print("File downloaded successfully.")
            print()
            file.close()
            resp_socket.close()

# This function returns the filename that we want to write.
def getfilename(data):
    path = data.split(' ')[1]
    return path.split('/')[-1]

# This function returns the response code of the response.
def getresponsecode(response):
    return response.decode().split(' ')[1]

if __name__ == "__main__":
    main()
