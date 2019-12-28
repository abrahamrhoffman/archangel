import configparser
import subprocess
import paramiko
import argparse
import base64
import glob
import sys


class Promote(object):

    '''
    Description   : This class promotes docker images to a discrete set of
                    servers enumerated in this class's constructor.

    Logic         : For every production server defined, ssh to the box.
                    Then, stop any container with the same name and download
                    the latest container from the docker registry. Next,
                    start the container in host networking mode, with any
                    specified backing volume. Once the container is running,
                    promotion is complete.

                    * No additional checks for ports, etc should be performed.
    '''

    def __init__(self, image):
        self.image = image
        self.container_name = image.split("/")[-1].split(":")[0]
        self.whoami, self.priv_key_file = self.get_sshkey()

        parser = configparser.ConfigParser()
        parser.read("authentication.ini")
        self.username = base64.b64decode(parser.get("production", "username"))
        self.prod_servers = parser.get("production", "servers")
        self.prod_servers = self.prod_servers.split("\n")
        self.dockerhub_username = base64.b64decode(
            parser.get("dockerhub", "username")).decode("utf-8")
        self.dockerhub_password = base64.b64decode(
            parser.get("dockerhub", "password")).decode("utf-8")

    def get_sshkey(self):
        whoami = subprocess.check_output("whoami", shell=True)
        whoami = (whoami.decode("utf-8")).split("\n")[0]
        # Convert OPENSSH key to usable Paramiko RSA ID:
        # `ssh-keygen -p -m PEM -f ~/.ssh/id_rsa`
        priv_key_file = ("/Users/{}/.ssh/id_rsa".format(whoami))
        return (whoami, priv_key_file)

    def start_session(self, server):
        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname=server,
                           username=self.username,
                           key_filename=self.priv_key_file)
            print("{}: ".format(server) +
                  "--- started session ---")
            return (client)
        except paramiko.ssh_exception.AuthenticationException:
            print("{}: Authentication Failure!".format(server))
            sys.exit(0)

    def login_dockerhub(self, server, client):
        cmd = ("docker login " +
               "--username '{}' ".format(self.dockerhub_username) +
               "--password '{}'".format(self.dockerhub_password))
        (stdin, stdout, stderr) = client.exec_command(cmd)
        for line in stdout:
            print("{}: ".format(server) +
                  line.strip('\n'))
        for line in stderr:
            print("{}: [stderr] ".format(server) +
                  line.strip("\n"))

    def stop_container(self, server, client):
        cmd = ("docker stop {}".format(self.container_name))
        (stdin, stdout, stderr) = client.exec_command(cmd)
        for line in stdout:
            print("{}: ".format(server) +
                  line.strip('\n'))
        cmd = ("docker rm {}".format(self.container_name))
        (stdin, stdout, stderr) = client.exec_command(cmd)
        for line in stdout:
            print("{}: ".format(server) +
                  line.strip("\n"))
        for line in stderr:
            print("{}: [stderr] ".format(server) +
                  line.strip("\n"))

    def remove_container_image(self, server, client):
        cmd = ("for IMAGE in " +
               "`docker images | grep -v 'REPOSITORY' | " +
               "grep '{}' | ".format(self.container_name) +
               "awk '{print $3}'`;" +
               "do docker rmi -f $IMAGE;done")
        (stdin, stdout, stderr) = client.exec_command(cmd)
        for line in stdout:
            print("{}: ".format(server) +
                  line.strip("\n"))
        for line in stderr:
            print("{}: [stderr] ".format(server) +
                  line.strip("\n"))

    def pull_container_image(self, server, client):
        cmd = ("docker pull {}".format(self.image))
        (stdin, stdout, stderr) = client.exec_command(cmd)
        for line in stdout:
            print("{}: ".format(server) +
                  line.strip("\n"))
        for line in stderr:
            print("{}: [stderr] ".format(server) +
                  line.strip("\n"))

    def start_container(self, server, client, volume=str("")):
        cmd = ("docker run --name {} ".format(self.container_name) +
               "--network host " +
               "--privileged " +
               "-td {}".format(self.image))
        (stdin, stdout, stderr) = client.exec_command(cmd)
        for line in stdout:
            print("{}: ".format(server) +
                  line.strip("\n"))
        for line in stderr:
            print("{}: [stderr] ".format(server) +
                  line.strip("\n"))

    def end_session(self, server, client):
        client.close()
        print("{}: ".format(server) +
              "--- ended session ---")

    def run(self):
        for server in self.prod_servers:
            client = self.start_session(server)
            self.login_dockerhub(server, client)
            self.stop_container(server, client)
            self.remove_container_image(server, client)
            self.pull_container_image(server, client)
            self.start_container(server, client)
            self.end_session(server, client)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-i",
                        "--image",
                        required=True,
                        action="store",
                        help="Image:Tag")
    args = parser.parse_args()
    promote = Promote(args.image)
    promote.run()


if __name__ == "__main__":
    main()
