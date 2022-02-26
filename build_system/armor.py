# -*- coding: utf-8 -*-
# @Author: lnorb.com
# @Date:   2022-01-28 05:46:08
# @Last Modified by:   lnorb.com
# @Last Modified time: 2022-02-26 14:23:31

try:
    # not all actions install all requirements
    import os
    from invoke import task
    from pathlib import Path
    import requests
    import zipfile
    from fabric import Connection
    import git
    import yaml
    import logging
    import boto3
    from botocore.exceptions import ClientError
    import rsa
except:
    pass

name = "lnorb"
VERSION = open("VERSION").read().strip()


def upload_to_s3(env, file_name, bucket, object_name=None):
    if object_name is None:
        object_name = os.path.basename(file_name)
    s3_client = boto3.client(
        "s3",
        aws_access_key_id=env["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=env["AWS_SECRET_ACCESS_KEY"],
    )
    try:
        response = s3_client.upload_file(
            file_name, bucket, object_name, ExtraArgs={"ACL": "public-read"}
        )
    except ClientError as e:
        logging.error(e)
        return False
    return True


def zipdir(path, ziph):
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(
                os.path.join(root, file),
                os.path.relpath(os.path.join(root, file), path),
            )


@task
def register(c, env=os.environ):
    c.run("pyarmor register pyarmor-regcode-2364.txt", env=env)


def ubuntu_boostrap_3_9():
    return """\
#!/bin/bash

sudo apt-get update;
sudo apt-get -y install python3-pip;
sudo apt update -y;
sudo apt install software-properties-common  -y;
sudo add-apt-repository ppa:deadsnakes/ppa  -y;
sudo apt install python3.9  -y;
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py;
sudo python3.9 get-pip.py;
pip3.9 install kivymd==0.104.2 --user;
pip3.9 install peewee==3.14.8 --user;
pip3.9 install python-dateutil==2.8.2 --user;
pip3.9 install kivy_garden.graph==0.4.0 --user;
pip3.9 install PyYaml==6.0 --user;
pip3.9 install simplejson==3.17.6 --user;
pip3.9 install Kivy==2.0.0 --user;
pip3.9 install google-api-python-client --user;
pip3.9 install grpcio --user;
pip3.9 install ffpyplayer==4.2.0 --user;
pip3.9 install python-dateutil==2.8.2 --user;
pip3.9 install pyinstaller --user;
pip3.9 install pyarmor==6.6.2 --user;
pip3.9 install fabric --user;
pip3.9 install plyer --user;
pip3.9 install semver --user;
pip3.9 install matplotlib --user;
pip3.9 install pandas --user;
    """


def upload(path):
    cert = (Path(os.getcwd()) / "lnorb_com.cer").as_posix()
    with Connection(
        "lnorb.com", connect_kwargs={"key_filename": cert}, user="ubuntu"
    ) as con:
        con.put(path, "/home/ubuntu/lnorb_com/releases/")


def build_common(c, env, sep=":"):
    register(c)
    spec = ""
    if spec == ";":
        # windows detected
        spec = "-s lnorb-win-patched.spec"
    paths = " ".join(
        [
            f"--paths={x.as_posix()}"
            for x in Path("third_party/").glob("*")
            if x.is_dir()
        ]
    )

    data = [
        ("orb/lnd/grpc_generated", "orb/lnd/grpc_generated"),
        ("orb/images/shadow_inverted.png", "orb/images/"),
        ("orb/misc/settings.json", "orb/misc/"),
        ("orb/apps/auto_fees/autofees.py", "orb/apps/auto_fees/"),
        ("orb/apps/auto_fees/autofees.kv", "orb/apps/auto_fees/"),
        ("orb/apps/auto_fees/autofees.png", "orb/apps/auto_fees/"),
        ("orb/apps/auto_fees/appinfo.yaml", "orb/apps/auto_fees/"),
        ("orb/apps/auto_rebalance/autobalance.py", "orb/apps/auto_rebalance/"),
        ("orb/apps/auto_rebalance/autobalance.kv", "orb/apps/auto_rebalance/"),
        ("orb/apps/auto_rebalance/autobalance.png", "orb/apps/auto_rebalance/"),
        ("orb/apps/auto_rebalance/appinfo.yaml", "orb/apps/auto_rebalance/"),
        ("orb/apps/auto_max_htlcs/update_max_htlc.py", "orb/apps/auto_max_htlcs/"),
        ("orb/apps/auto_max_htlcs/update_max_htlcs.png", "orb/apps/auto_max_htlcs/"),
        ("orb/apps/auto_max_htlcs/appinfo.yaml", "orb/apps/auto_max_htlcs/"),
        ("video_library.yaml", "."),
        ("images/ln.png", "images/"),
    ]
    data = " ".join(f"--add-data '{s}{sep}{d}'" for s, d in data)
    hidden_imports = "--hidden-import orb.kvs --hidden-import orb.misc --hidden-import kivymd.effects.stiffscroll.StiffScrollEffect --hidden-import pandas.plotting._matplotlib --hidden-import=pkg_resources"
    pyinstall_flags = f" {paths} {data} {hidden_imports} --onedir --windowed "
    c.run(
        f"""pyarmor pack {spec} --with-license outer --name {name} \
             -e " {pyinstall_flags}" \
             -x " --no-cross-protection --exclude build --exclude orb/lnd/grpc_generated" main.py""",
        env=env,
    )


@task
def build_linux(c, env=os.environ):
    register(c)
    c.run("rm -rf dist tmp;")
    c.run("mkdir -p tmp;")
    c.run("cp -r main.py tmp/;")
    c.run("cp -r third_party tmp/;")
    c.run("cp -r orb tmp/;")
    with c.cd("tmp"):
        c.run(
            "pyarmor obfuscate --with-license outer --recursive main.py;",
            env=env,
        )
        c.run("rm -rf orb main.py third_party")
        c.run("mv dist orb")
        with open("tmp/orb/bootstrap.sh", "w") as f:
            f.write(ubuntu_boostrap_3_9())
        build_name = f"orb-{VERSION}-{os.environ['os-name']}-x86_64.tar.gz"
        c.run(f"tar czvf {build_name} orb;")
        upload_to_s3(
            env,
            f"tmp/{build_name}",
            "lnorb",
            object_name=f"customer_builds/{build_name}",
        )


@task
def build_osx(c, do_upload=True, env=os.environ):
    build_common(c=c, env=env, sep=":")
    file_name = dmg(c=c, env=env)
    if do_upload:
        print(f"Uploading {file_name} to S3: customer_builds/{file_name}")
        upload_to_s3(
            env, file_name, "lnorb", object_name=f"customer_builds/{file_name}"
        )


@task
def build_windows(c, env=os.environ):
    build_common(c, env, ";")
    build_name = f"orb-{VERSION}-{os.environ['os-name']}-x86_64.zip"
    zipf = zipfile.ZipFile(build_name, "w", zipfile.ZIP_DEFLATED)
    # for p in Path(".").glob("*.spec"):
    #     print(p)
    #     print(p.open().read())
    # shutil.copyfile(p.as_posix(), "dist")
    zipdir("dist", zipf)
    zipf.close()
    upload_to_s3(env, build_name, "lnorb", object_name=f"customer_builds/{build_name}")


def dmg(c, env=os.environ):
    c.run("rm -f *.dmg ")
    c.run(
        f"""
        create-dmg \
          --volname "Orb" \
          --background "images/bg.jpeg" \
          --window-pos 200 120 \
          --window-size 800 400 \
          --icon-size 100 \
          --icon "lnorb.app" 200 190 \
          --app-drop-link 600 185 \
          "{name}.dmg" \
          "dist/{name}.app"
        """,
        env=env,
    )
    build_name = f"orb-{VERSION}-{os.environ.get('os-name', 'macos-11')}-x86_64.dmg"
    os.rename(f"{name}.dmg", build_name)
    return build_name
