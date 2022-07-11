from typing import Union, TextIO, Sequence, Optional
import argparse
import base64
import json
import os
import sys
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
Parser = argparse.ArgumentParser
Args = argparse.Namespace
ParserError = argparse.ArgumentError


def generate_private_key(key_size: int = 2048, public_exponent=65537) -> RSAPrivateKey:
    key = rsa.generate_private_key(
        key_size=key_size, public_exponent=public_exponent)
    return key


def save_key(key: RSAPrivateKey, file_name: str = "key.pem", save_public: bool = False, public_file_name: str = "key.pub.pem",
             override_existing: bool = False, passphrase: Optional[str] = None):
    dest_file = os.path(file_name)
    if not override_existing and os.path.isfile(dest_file):
        raise FileExistsError(f"A private key already exists in {file_name}")
    # write private key
    encryption_algorithm = serialization.NoEncryption if passphrase is None else serialization.BestAvailableEncryption(
        password=passphrase.encode("utf8"))
    with open(dest_file, "w") as fout:
        fout.write(key.private_bytes(encoding=serialization.Encoding.PEM,
                                     format=serialization.PrivateFormat.TraditionalOpenSSL,
                                     encryption_algorithm=encryption_algorithm))
    if save_public:
        if os.path.exists(public_file_name):
            raise FileExistsError(
                f"A public key already exists in {public_file_name}")
        pub_key: RSAPublicKey = key.public_key()
        with open(public_file_name, "w") as fout:
            fout.write(
                pub_key.public_bytes(encoding=serialization.Encoding.PEM,
                                     format=serialization.PublicFormat.PKCS1)
            )


def base64_encode(data: bytes, url_variant: bool = False) -> bytes:
    encode_func = base64.b64encode if not url_variant else base64.urlsafe_b64encode
    return encode_func(data)


def base64_decode(data: bytes, url_variant: bool = False) -> bytes:
    decode_func = base64.urlsafe_b64decode if url_variant else base64.b64decode
    return decode_func(data)


def write_output(data: Sequence[Union[bytes, str]], out_device: Union[str, TextIO], format: str = "txt"):
    if isinstance(out_device, str):
        with open(out_device, "w") as woout:
            woout.writelines(f"{d}\n" if isinstance(
                d, str) else str(d) for d in data)
    else:
        out_device.writelines(f"{d}\n" if isinstance(
            d, str) else str(d) for d in data)


def parse_args():
    p: Parser = Parser()
    cmd_group = p.add_argument_group()
    p.add_argument(
        "-u", "--url", help="use base64 url friendly variant", action='store_true')
    p.add_argument("-e", "--encoding",
                   help="string encoding format ( default utf-8 )", default="utf8")
    p.add_argument(
        "-o", "--output", help="output to write to (default stdout)", default=sys.stdout)
    p.add_argument("-f", "--format", help="output format",
                   choices=("txt", "json"))
    p.add_argument("input_data", help="string to b64encode")
    return p.parse_args()


def run_main():
    args = parse_args()
    data_str: str = args.input_data
    data_encoding = args.encoding
    data = data_str.encode(encoding=data_encoding)
    b64_data = base64_encode(data=data, url_variant=args.url)
    b64_data_str = b64_data.decode(encoding=data_encoding)
    write_output(data=[b64_data, b64_data_str], out_device=sys.stdout)
    # if not args.output or args.output == sys.stdout:
    #     print(f"{b64_data=}\n{b64_data_str=}")
    # else:
    #     print(f"Writing to file {args.output}")
    #     with open(args.output, "w") as fout:
    #         fout.write(f"{b64_data=}\n{b64_data_str=}")


if __name__ == "__main__":
    run_main()
