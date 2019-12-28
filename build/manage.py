import configparser
import subprocess
import argparse
import shutil
import base64
import glob
import sys
import os

import promote


class Manage(object):

    def __init__(self, image, verbose=False):
        self.init_feedback()
        self.verbose = verbose
        self.devnull = open(os.devnull, "w")
        self.image = image
        parser = configparser.ConfigParser()
        parser.read("authentication.ini")
        self.dockerhub_username = base64.b64decode(
            parser.get("dockerhub", "username")).decode("utf-8")
        self.dockerhub_password = base64.b64decode(
            parser.get("dockerhub", "password")).decode("utf-8")
        self.dockerhub_priv_username = base64.b64decode(
            parser.get("dockerhub_priv", "username")).decode("utf-8")
        self.dockerhub_priv_password = base64.b64decode(
            parser.get("dockerhub_priv", "password")).decode("utf-8")

    def init_feedback(self):
        print("#########################")
        print("#  Void Build Pipeline  #")
        print("#########################")

    def docker_login_pub(self):
        cmd = ("docker login " +
               "--username {} ".format(self.dockerhub_username) +
               "--password {}".format(self.dockerhub_password))
        subprocess.call(cmd, shell=True)

    def docker_login_priv(self):
        cmd = ("docker login dockerhub.paypalcorp.com:443 " +
               "--username {} ".format(self.dockerhub_priv_username) +
               "--password {}".format(self.dockerhub_priv_password))
        subprocess.call(cmd, shell=True)

    def build(self):
        sys.stdout.write("Building Container... ")
        sys.stdout.flush()
        cmd = ("docker build -t {} ../"
               .format(self.image))
        if self.verbose:
            subprocess.call(cmd, shell=True)
        else:
            subprocess.call(cmd,
                            stdout=self.devnull,
                            stderr=self.devnull,
                            shell=True)
        sys.stdout.write("Done")
        sys.stdout.flush()
        print("")

    def push(self):
        sys.stdout.write("Pushing Container... ")
        sys.stdout.flush()
        cmd = ("docker push {}"
               .format(self.image))
        if self.verbose:
            subprocess.call(cmd, shell=True)
        else:
            subprocess.call(cmd,
                            stdout=self.devnull,
                            stderr=self.devnull,
                            shell=True)
        sys.stdout.write("Done")
        sys.stdout.flush()
        print("")

    def promote(self):
        sys.stdout.write("Promoting Container... ")
        sys.stdout.flush()
        prom = promote.Promote(self.image)
        prom.run()
        sys.stdout.write("Done")
        sys.stdout.flush()

    def clean(self):
        files_to_remove = glob.glob("./*.pyc")
        for aFile in files_to_remove:
            os.remove(aFile)
        shutil.rmtree("__pycache__")

    def run(self):
        self.docker_login_pub()
        self.build()
        self.push()
        self.promote()
        self.clean()
        self.docker_login_priv()


def main():
    parser = argparse.ArgumentParser()
    required = parser.add_argument_group('Required arguments')
    required.add_argument("-i",
                          "--image",
                          action="store",
                          help="Docker image and tag",
                          required=True)
    required.add_argument("-v",
                          "--verbose",
                          action="store_true",
                          help="Show output (default False)")
    args = parser.parse_args()
    if args.verbose:
        manage = Manage(args.image, args.verbose)
    else:
        manage = Manage(args.image)
    manage.run()


if __name__ == "__main__":
    main()
