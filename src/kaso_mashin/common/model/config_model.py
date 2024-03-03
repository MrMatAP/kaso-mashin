import typing
import pydantic

Predefined_Images = {
    'ubuntu-bionic': 'https://cloud-images.ubuntu.com/bionic/current/bionic-server-cloudimg-arm64.img',
    'ubuntu-focal': 'https://cloud-images.ubuntu.com/focal/current/focal-server-cloudimg-arm64.img',
    'ubuntu-jammy': 'https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-arm64.img',
    'ubuntu-kinetic': 'https://cloud-images.ubuntu.com/kinetic/current/kinetic-server-cloudimg-arm64.img',
    'ubuntu-lunar': 'https://cloud-images.ubuntu.com/lunar/current/lunar-server-cloudimg-arm64.img',
    'ubuntu-mantic': 'https://cloud-images.ubuntu.com/mantic/current/mantic-server-cloudimg-arm64.img',
    'freebsd-14': 'https://download.freebsd.org/ftp/snapshots/VM-IMAGES/14.0-CURRENT/amd64/Latest/'
                  'FreeBSD-14.0-CURRENT-amd64.qcow2.xz',
    'flatcar-arm64': 'https://stable.release.flatcar-linux.net/arm64-usr/current/flatcar_production_qemu_uefi_image.img',
    'flatcar-amd64': 'https://stable.release.flatcar-linux.net/amd64-usr/current/flatcar_production_qemu_image.img'
}


class ImagePredefinedSchema(pydantic.BaseModel):
    """
    Output schema to get a list of predefined images
    """
    name: str = pydantic.Field(description='The image name', examples=['ubuntu-jammy'])
    url: str = pydantic.Field(description='The image URL',
                              examples=[
                                  'https://cloud-images.ubuntu.com/jammy/current/jammy-server-cloudimg-arm64.img'])


class ConfigSchema(pydantic.BaseModel):
    """
    Configuration Schema
    """
    version: str = pydantic.Field(description='The version of the kaso-mashin server',
                                  examples=['1.0.0'])
    predefined_images: typing.List[ImagePredefinedSchema] = pydantic.Field(description='List of predefined images',
                                                                           default=[])
