# SPDX-FileCopyrightText: 2014 MicroPython & CircuitPython contributors (https://github.com/adafruit/circuitpython/graphs/contributors)
#
# SPDX-License-Identifier: MIT

import argparse

import os
import sys

sys.path.append("../../tools/usb_descriptor")

from adafruit_usb_descriptor import audio, audio10, cdc, hid, midi, msc, standard, util
import hid_report_descriptors

DEFAULT_INTERFACE_NAME = "CircuitPython"
ALL_DEVICES = "CDC CDC2 MSC AUDIO HID VENDOR"
ALL_DEVICES_SET = frozenset(ALL_DEVICES.split())
DEFAULT_DEVICES = "CDC MSC AUDIO HID"

ALL_HID_DEVICES = (
    "KEYBOARD MOUSE CONSUMER SYS_CONTROL GAMEPAD DIGITIZER XAC_COMPATIBLE_GAMEPAD RAW SPACEMOUSE"
)
ALL_HID_DEVICES_SET = frozenset(ALL_HID_DEVICES.split())
# Digitizer works on Linux but conflicts with mouse, so omit it.
DEFAULT_HID_DEVICES = "KEYBOARD MOUSE CONSUMER GAMEPAD SPACEMOUSE"

# In the following URL, don't include the https:// because that prefix gets added automatically
DEFAULT_WEBUSB_URL = (
    "circuitpython.org"  # In the future, this may become a specific landing page
)

parser = argparse.ArgumentParser(description="Generate USB descriptors.")
parser.add_argument(
    "--highspeed",
    default=False,
    action="store_true",
    help="descriptor for highspeed device",
)
parser.add_argument("--manufacturer", type=str, help="manufacturer of the device")
parser.add_argument("--product", type=str, help="product name of the device")
parser.add_argument("--vid", type=lambda x: int(x, 16), help="vendor id")
parser.add_argument("--pid", type=lambda x: int(x, 16), help="product id")
parser.add_argument(
    "--serial_number_length",
    type=int,
    default=32,
    help="length needed for the serial number in digits",
)
parser.add_argument(
    "--devices",
    type=lambda l: tuple(l.split()),
    default=DEFAULT_DEVICES,
    help="devices to include in descriptor (AUDIO includes MIDI support)",
)
parser.add_argument(
    "--hid_devices",
    type=lambda l: tuple(l.split()),
    default=DEFAULT_HID_DEVICES,
    help="HID devices to include in HID report descriptor",
)
parser.add_argument(
    "--interface_name",
    type=str,
    help="The name/prefix to use in the interface descriptions",
    default=DEFAULT_INTERFACE_NAME,
)
parser.add_argument(
    "--no-renumber_endpoints",
    dest="renumber_endpoints",
    action="store_false",
    help="use to not renumber endpoint",
)
parser.add_argument(
    "--cdc_ep_num_notification",
    type=int,
    default=0,
    help="endpoint number of CDC NOTIFICATION",
)
parser.add_argument(
    "--cdc2_ep_num_notification",
    type=int,
    default=0,
    help="endpoint number of CDC2 NOTIFICATION",
)
parser.add_argument(
    "--cdc_ep_num_data_out", type=int, default=0, help="endpoint number of CDC DATA OUT"
)
parser.add_argument(
    "--cdc_ep_num_data_in", type=int, default=0, help="endpoint number of CDC DATA IN"
)
parser.add_argument(
    "--cdc2_ep_num_data_out",
    type=int,
    default=0,
    help="endpoint number of CDC2 DATA OUT",
)
parser.add_argument(
    "--cdc2_ep_num_data_in", type=int, default=0, help="endpoint number of CDC2 DATA IN"
)
parser.add_argument(
    "--msc_ep_num_out", type=int, default=0, help="endpoint number of MSC OUT"
)
parser.add_argument(
    "--msc_ep_num_in", type=int, default=0, help="endpoint number of MSC IN"
)
parser.add_argument(
    "--hid_ep_num_out", type=int, default=0, help="endpoint number of HID OUT"
)
parser.add_argument(
    "--hid_ep_num_in", type=int, default=0, help="endpoint number of HID IN"
)
parser.add_argument(
    "--midi_ep_num_out", type=int, default=0, help="endpoint number of MIDI OUT"
)
parser.add_argument(
    "--midi_ep_num_in", type=int, default=0, help="endpoint number of MIDI IN"
)
parser.add_argument(
    "--max_ep", type=int, default=0, help="total number of endpoints available"
)
parser.add_argument(
    "--webusb_url",
    type=str,
    help="The URL to include in the WebUSB URL Descriptor",
    default=DEFAULT_WEBUSB_URL,
)
parser.add_argument(
    "--vendor_ep_num_out", type=int, default=0, help="endpoint number of VENDOR OUT"
)
parser.add_argument(
    "--vendor_ep_num_in", type=int, default=0, help="endpoint number of VENDOR IN"
)
parser.add_argument(
    "--output_c_file", type=argparse.FileType("w", encoding="UTF-8"), required=True
)
parser.add_argument(
    "--output_h_file", type=argparse.FileType("w", encoding="UTF-8"), required=True
)

args = parser.parse_args()

unknown_devices = list(frozenset(args.devices) - ALL_DEVICES_SET)
if unknown_devices:
    raise ValueError("Unknown device(s)", unknown_devices)

unknown_hid_devices = list(frozenset(args.hid_devices) - ALL_HID_DEVICES_SET)
if unknown_hid_devices:
    raise ValueError("Unknown HID devices(s)", unknown_hid_devices)

include_cdc = "CDC" in args.devices
include_cdc2 = "CDC2" in args.devices
include_msc = "MSC" in args.devices
include_hid = "HID" in args.devices
include_audio = "AUDIO" in args.devices
include_vendor = "VENDOR" in args.devices

if not include_cdc and include_cdc2:
    raise ValueError("CDC2 requested without CDC")

if not args.renumber_endpoints:
    if include_cdc:
        if args.cdc_ep_num_notification == 0:
            raise ValueError("CDC notification endpoint number must not be 0")
        if args.cdc_ep_num_data_out == 0:
            raise ValueError("CDC data OUT endpoint number must not be 0")
        if args.cdc_ep_num_data_in == 0:
            raise ValueError("CDC data IN endpoint number must not be 0")

    if include_cdc2:
        if args.cdc2_ep_num_notification == 0:
            raise ValueError("CDC2 notification endpoint number must not be 0")
        if args.cdc2_ep_num_data_out == 0:
            raise ValueError("CDC2 data OUT endpoint number must not be 0")
        if args.cdc2_ep_num_data_in == 0:
            raise ValueError("CDC2 data IN endpoint number must not be 0")

    if include_msc:
        if args.msc_ep_num_out == 0:
            raise ValueError("MSC endpoint OUT number must not be 0")
        if args.msc_ep_num_in == 0:
            raise ValueError("MSC endpoint IN number must not be 0")

    if include_hid:
        if args.args.hid_ep_num_out == 0:
            raise ValueError("HID endpoint OUT number must not be 0")
        if args.hid_ep_num_in == 0:
            raise ValueError("HID endpoint IN number must not be 0")

    if include_audio:
        if args.args.midi_ep_num_out == 0:
            raise ValueError("MIDI endpoint OUT number must not be 0")
        if args.midi_ep_num_in == 0:
            raise ValueError("MIDI endpoint IN number must not be 0")

    if include_vendor:
        if args.vendor_ep_num_out == 0:
            raise ValueError("VENDOR endpoint OUT number must not be 0")
        if args.vendor_ep_num_in == 0:
            raise ValueError("VENDOR endpoint IN number must not be 0")


class StringIndex:
    """Assign a monotonically increasing index to each unique string. Start with 0."""

    string_to_index = {}
    index_to_variable = {}
    strings = []

    @classmethod
    def index(cls, string, *, variable_name=None):
        if string in cls.string_to_index:
            idx = cls.string_to_index[string]
            if not cls.index_to_variable[idx]:
                cls.index_to_variable[idx] = variable_name
            return idx
        else:
            idx = len(cls.strings)
            cls.string_to_index[string] = idx
            cls.strings.append(string)
            cls.index_to_variable[idx] = variable_name
            return idx

    @classmethod
    def strings_in_order(cls):
        return cls.strings


# langid must be the 0th string descriptor
LANGID_INDEX = StringIndex.index("\u0409", variable_name="language_id")
assert LANGID_INDEX == 0
SERIAL_NUMBER_INDEX = StringIndex.index(
    "S" * args.serial_number_length, variable_name="usb_serial_number"
)

device = standard.DeviceDescriptor(
    description="top",
    idVendor=args.vid,
    idProduct=args.pid,
    iManufacturer=StringIndex.index(args.manufacturer),
    iProduct=StringIndex.index(args.product),
    iSerialNumber=SERIAL_NUMBER_INDEX,
)

# Interface numbers are interface-set local and endpoints are interface local
# until util.join_interfaces renumbers them.


def make_cdc_union(name):
    return cdc.Union(
        description="{} comm".format(name),
        # Set bMasterInterface and bSlaveInterface_list to proper values after interfaces are renumbered.
        bMasterInterface=0x00,
        bSlaveInterface_list=[0x01],
    )


def make_cdc_call_management(name):
    # Set bDataInterface to proper value after interfaces are renumbered.
    return cdc.CallManagement(
        description="{} comm".format(name), bmCapabilities=0x01, bDataInterface=0x01
    )


def make_cdc_comm_interface(
    name, cdc_union, cdc_call_management, cdc_ep_num_notification
):
    return standard.InterfaceDescriptor(
        description="{} comm".format(name),
        bInterfaceClass=cdc.CDC_CLASS_COMM,  # Communications Device Class
        bInterfaceSubClass=cdc.CDC_SUBCLASS_ACM,  # Abstract control model
        bInterfaceProtocol=cdc.CDC_PROTOCOL_NONE,
        iInterface=StringIndex.index("{} {} control".format(args.interface_name, name)),
        subdescriptors=[
            cdc.Header(description="{} comm".format(name), bcdCDC=0x0110),
            cdc_call_management,
            cdc.AbstractControlManagement(
                description="{} comm".format(name), bmCapabilities=0x02
            ),
            cdc_union,
            standard.EndpointDescriptor(
                description="{} comm in".format(name),
                bEndpointAddress=cdc_ep_num_notification
                | standard.EndpointDescriptor.DIRECTION_IN,
                bmAttributes=standard.EndpointDescriptor.TYPE_INTERRUPT,
                wMaxPacketSize=0x0040,
                bInterval=0x10,
            ),
        ],
    )


def make_cdc_data_interface(name, cdc_ep_num_data_in, cdc_ep_num_data_out):
    return standard.InterfaceDescriptor(
        description="{} data".format(name),
        bInterfaceClass=cdc.CDC_CLASS_DATA,
        iInterface=StringIndex.index("{} {} data".format(args.interface_name, name)),
        subdescriptors=[
            standard.EndpointDescriptor(
                description="{} data out".format(name),
                bEndpointAddress=cdc_ep_num_data_out
                | standard.EndpointDescriptor.DIRECTION_OUT,
                bmAttributes=standard.EndpointDescriptor.TYPE_BULK,
                bInterval=0,
                wMaxPacketSize=512 if args.highspeed else 64,
            ),
            standard.EndpointDescriptor(
                description="{} data in".format(name),
                bEndpointAddress=cdc_ep_num_data_in
                | standard.EndpointDescriptor.DIRECTION_IN,
                bmAttributes=standard.EndpointDescriptor.TYPE_BULK,
                bInterval=0,
                wMaxPacketSize=512 if args.highspeed else 64,
            ),
        ],
    )


if include_cdc:
    cdc_union = make_cdc_union("CDC")
    cdc_call_management = make_cdc_call_management("CDC")
    cdc_comm_interface = make_cdc_comm_interface(
        "CDC", cdc_union, cdc_call_management, args.cdc_ep_num_notification
    )
    cdc_data_interface = make_cdc_data_interface(
        "CDC", args.cdc_ep_num_data_in, args.cdc_ep_num_data_out
    )

    cdc_interfaces = [cdc_comm_interface, cdc_data_interface]

if include_cdc2:
    cdc2_union = make_cdc_union("CDC2")
    cdc2_call_management = make_cdc_call_management("CDC2")
    cdc2_comm_interface = make_cdc_comm_interface(
        "CDC2", cdc2_union, cdc2_call_management, args.cdc2_ep_num_notification
    )
    cdc2_data_interface = make_cdc_data_interface(
        "CDC2", args.cdc2_ep_num_data_in, args.cdc2_ep_num_data_out
    )

    cdc2_interfaces = [cdc2_comm_interface, cdc2_data_interface]

if include_msc:
    msc_interfaces = [
        standard.InterfaceDescriptor(
            description="MSC",
            bInterfaceClass=msc.MSC_CLASS,
            bInterfaceSubClass=msc.MSC_SUBCLASS_TRANSPARENT,
            bInterfaceProtocol=msc.MSC_PROTOCOL_BULK,
            iInterface=StringIndex.index("{} Mass Storage".format(args.interface_name)),
            subdescriptors=[
                standard.EndpointDescriptor(
                    description="MSC in",
                    bEndpointAddress=args.msc_ep_num_in
                    | standard.EndpointDescriptor.DIRECTION_IN,
                    bmAttributes=standard.EndpointDescriptor.TYPE_BULK,
                    bInterval=0,
                    wMaxPacketSize=512 if args.highspeed else 64,
                ),
                standard.EndpointDescriptor(
                    description="MSC out",
                    bEndpointAddress=(
                        args.msc_ep_num_out | standard.EndpointDescriptor.DIRECTION_OUT
                    ),
                    bmAttributes=standard.EndpointDescriptor.TYPE_BULK,
                    bInterval=0,
                    wMaxPacketSize=512 if args.highspeed else 64,
                ),
            ],
        )
    ]


if include_hid:
    # When there's only one hid_device, it shouldn't have a report id.
    # Otherwise, report ids are assigned sequentially:
    # args.hid_devices[0] has report_id 1
    # args.hid_devices[1] has report_id 2
    # etc.

    report_ids = {}

    if len(args.hid_devices) == 1:
        name = args.hid_devices[0]
        combined_hid_report_descriptor = hid.ReportDescriptor(
            description=name,
            report_descriptor=bytes(
                hid_report_descriptors.REPORT_DESCRIPTOR_FUNCTIONS[name](0)
            ),
        )
        report_ids[name] = 0
    else:
        report_id = 1
        concatenated_descriptors = bytearray()
        for name in args.hid_devices:
            concatenated_descriptors.extend(
                bytes(
                    hid_report_descriptors.REPORT_DESCRIPTOR_FUNCTIONS[name](report_id)
                )
            )
            report_ids[name] = report_id
            report_id += 1
        combined_hid_report_descriptor = hid.ReportDescriptor(
            description="MULTIDEVICE", report_descriptor=bytes(concatenated_descriptors)
        )

    # ASF4 expects keyboard and generic devices to have both in and out endpoints,
    # and will fail (possibly silently) if both are not supplied.
    hid_endpoint_in_descriptor = standard.EndpointDescriptor(
        description="HID in",
        bEndpointAddress=args.hid_ep_num_in | standard.EndpointDescriptor.DIRECTION_IN,
        bmAttributes=standard.EndpointDescriptor.TYPE_INTERRUPT,
        bInterval=8,
    )

    hid_endpoint_out_descriptor = standard.EndpointDescriptor(
        description="HID out",
        bEndpointAddress=args.hid_ep_num_out
        | standard.EndpointDescriptor.DIRECTION_OUT,
        bmAttributes=standard.EndpointDescriptor.TYPE_INTERRUPT,
        bInterval=8,
    )

    hid_interfaces = [
        standard.InterfaceDescriptor(
            description="HID Multiple Devices",
            bInterfaceClass=hid.HID_CLASS,
            bInterfaceSubClass=hid.HID_SUBCLASS_NOBOOT,
            bInterfaceProtocol=hid.HID_PROTOCOL_NONE,
            iInterface=StringIndex.index("{} HID".format(args.interface_name)),
            subdescriptors=[
                hid.HIDDescriptor(
                    description="HID",
                    wDescriptorLength=len(bytes(combined_hid_report_descriptor)),
                ),
                hid_endpoint_in_descriptor,
                hid_endpoint_out_descriptor,
            ],
        ),
    ]

if include_audio:
    # Audio!
    # In and out here are relative to CircuitPython

    # USB OUT -> midi_in_jack_emb -> midi_out_jack_ext -> CircuitPython
    midi_in_jack_emb = midi.InJackDescriptor(
        description="MIDI PC -> {}".format(args.interface_name),
        bJackType=midi.JACK_TYPE_EMBEDDED,
        iJack=StringIndex.index("{} usb_midi.ports[0]".format(args.interface_name)),
    )
    midi_out_jack_ext = midi.OutJackDescriptor(
        description="MIDI data out to user code.",
        bJackType=midi.JACK_TYPE_EXTERNAL,
        input_pins=[(midi_in_jack_emb, 1)],
        iJack=0,
    )

    # USB IN <- midi_out_jack_emb <- midi_in_jack_ext <- CircuitPython
    midi_in_jack_ext = midi.InJackDescriptor(
        description="MIDI data in from user code.",
        bJackType=midi.JACK_TYPE_EXTERNAL,
        iJack=0,
    )
    midi_out_jack_emb = midi.OutJackDescriptor(
        description="MIDI PC <- {}".format(args.interface_name),
        bJackType=midi.JACK_TYPE_EMBEDDED,
        input_pins=[(midi_in_jack_ext, 1)],
        iJack=StringIndex.index("{} usb_midi.ports[1]".format(args.interface_name)),
    )

    audio_midi_interface = standard.InterfaceDescriptor(
        description="Midi goodness",
        bInterfaceClass=audio.AUDIO_CLASS_DEVICE,
        bInterfaceSubClass=audio.AUDIO_SUBCLASS_MIDI_STREAMING,
        bInterfaceProtocol=audio.AUDIO_PROTOCOL_V1,
        iInterface=StringIndex.index("{} MIDI".format(args.interface_name)),
        subdescriptors=[
            midi.Header(
                jacks_and_elements=[
                    midi_in_jack_emb,
                    midi_in_jack_ext,
                    midi_out_jack_emb,
                    midi_out_jack_ext,
                ],
            ),
            standard.EndpointDescriptor(
                description="MIDI data out to {}".format(args.interface_name),
                bEndpointAddress=args.midi_ep_num_out
                | standard.EndpointDescriptor.DIRECTION_OUT,
                bmAttributes=standard.EndpointDescriptor.TYPE_BULK,
                bInterval=0,
                wMaxPacketSize=512 if args.highspeed else 64,
            ),
            midi.DataEndpointDescriptor(baAssocJack=[midi_in_jack_emb]),
            standard.EndpointDescriptor(
                description="MIDI data in from {}".format(args.interface_name),
                bEndpointAddress=args.midi_ep_num_in
                | standard.EndpointDescriptor.DIRECTION_IN,
                bmAttributes=standard.EndpointDescriptor.TYPE_BULK,
                bInterval=0x0,
                wMaxPacketSize=512 if args.highspeed else 64,
            ),
            midi.DataEndpointDescriptor(baAssocJack=[midi_out_jack_emb]),
        ],
    )

    cs_ac_interface = audio10.AudioControlInterface(
        description="Empty audio control",
        audio_streaming_interfaces=[],
        midi_streaming_interfaces=[audio_midi_interface],
    )

    audio_control_interface = standard.InterfaceDescriptor(
        description="All the audio",
        bInterfaceClass=audio.AUDIO_CLASS_DEVICE,
        bInterfaceSubClass=audio.AUDIO_SUBCLASS_CONTROL,
        bInterfaceProtocol=audio.AUDIO_PROTOCOL_V1,
        iInterface=StringIndex.index("{} Audio".format(args.interface_name)),
        subdescriptors=[
            cs_ac_interface,
        ],
    )

    # Audio streaming interfaces must occur before MIDI ones.
    audio_interfaces = (
        [audio_control_interface]
        + cs_ac_interface.audio_streaming_interfaces
        + cs_ac_interface.midi_streaming_interfaces
    )

if include_vendor:
    # Vendor-specific interface, for example WebUSB
    vendor_endpoint_in_descriptor = standard.EndpointDescriptor(
        description="VENDOR in",
        bEndpointAddress=args.vendor_ep_num_in
        | standard.EndpointDescriptor.DIRECTION_IN,
        bmAttributes=standard.EndpointDescriptor.TYPE_BULK,
        bInterval=16,
    )

    vendor_endpoint_out_descriptor = standard.EndpointDescriptor(
        description="VENDOR out",
        bEndpointAddress=args.vendor_ep_num_out
        | standard.EndpointDescriptor.DIRECTION_OUT,
        bmAttributes=standard.EndpointDescriptor.TYPE_BULK,
        bInterval=16,
    )

    vendor_interface = standard.InterfaceDescriptor(
        description="VENDOR",
        bInterfaceClass=0xFF,  # Vendor-specific
        bInterfaceSubClass=0x00,
        bInterfaceProtocol=0x00,
        iInterface=StringIndex.index("{} VENDOR".format(args.interface_name)),
        subdescriptors=[
            vendor_endpoint_in_descriptor,
            vendor_endpoint_out_descriptor,
        ],
    )

    vendor_interfaces = [vendor_interface]

interfaces_to_join = []

if include_cdc:
    interfaces_to_join.append(cdc_interfaces)

if include_cdc2:
    interfaces_to_join.append(cdc2_interfaces)

if include_msc:
    interfaces_to_join.append(msc_interfaces)

if include_hid:
    interfaces_to_join.append(hid_interfaces)

if include_audio:
    interfaces_to_join.append(audio_interfaces)

if include_vendor:
    interfaces_to_join.append(vendor_interfaces)

# util.join_interfaces() will renumber the endpoints to make them unique across descriptors,
# and renumber the interfaces in order. But we still need to fix up certain
# interface cross-references.
interfaces = util.join_interfaces(
    interfaces_to_join, renumber_endpoints=args.renumber_endpoints
)

if args.max_ep != 0:
    for interface in interfaces:
        for subdescriptor in interface.subdescriptors:
            endpoint_address = getattr(subdescriptor, "bEndpointAddress", 0) & 0x7F
            if endpoint_address >= args.max_ep:
                raise ValueError(
                    "Endpoint address %d of '%s' must be less than %d; you have probably run out of endpoints"
                    % (endpoint_address & 0x7F, interface.description, args.max_ep)
                )
else:
    print(
        "Unable to check whether maximum number of endpoints is respected",
        file=sys.stderr,
    )

# Now adjust the CDC interface cross-references.

if include_cdc:
    cdc_union.bMasterInterface = cdc_comm_interface.bInterfaceNumber
    cdc_union.bSlaveInterface_list = [cdc_data_interface.bInterfaceNumber]

    cdc_call_management.bDataInterface = cdc_data_interface.bInterfaceNumber

if include_cdc2:
    cdc2_union.bMasterInterface = cdc2_comm_interface.bInterfaceNumber
    cdc2_union.bSlaveInterface_list = [cdc2_data_interface.bInterfaceNumber]

    cdc2_call_management.bDataInterface = cdc2_data_interface.bInterfaceNumber


def make_cdc_iad(cdc_comm_interface, name):
    return standard.InterfaceAssociationDescriptor(
        description="{} IAD".format(name),
        bFirstInterface=cdc_comm_interface.bInterfaceNumber,
        bInterfaceCount=len(cdc_interfaces),
        bFunctionClass=cdc.CDC_CLASS_COMM,  # Communications Device Class
        bFunctionSubClass=cdc.CDC_SUBCLASS_ACM,  # Abstract control model
        bFunctionProtocol=cdc.CDC_PROTOCOL_NONE,
    )


if include_cdc:
    cdc_iad = make_cdc_iad(cdc_comm_interface, "CDC")
if include_cdc2:
    cdc2_iad = make_cdc_iad(cdc2_comm_interface, "CDC2")

descriptor_list = []

if include_cdc:
    # Put the CDC IAD just before the CDC interfaces.
    # There appears to be a bug in the Windows composite USB driver that requests the
    # HID report descriptor with the wrong interface number if the HID interface is not given
    # first. However, it still fetches the descriptor anyway. We could reorder the interfaces but
    # the Windows 7 Adafruit_usbser.inf file thinks CDC is at Interface 0, so we'll leave it
    # there for backwards compatibility.
    descriptor_list.append(cdc_iad)
    descriptor_list.extend(cdc_interfaces)

if include_cdc2:
    descriptor_list.append(cdc2_iad)
    descriptor_list.extend(cdc2_interfaces)

if include_msc:
    descriptor_list.extend(msc_interfaces)

if include_hid:
    descriptor_list.extend(hid_interfaces)

if include_audio:
    # Only add the control interface because other audio interfaces are managed by it to ensure the
    # correct ordering.
    descriptor_list.append(audio_control_interface)

if include_vendor:
    descriptor_list.extend(vendor_interfaces)

# Finally, build the composite descriptor.

configuration = standard.ConfigurationDescriptor(
    description="Composite configuration",
    wTotalLength=(
        standard.ConfigurationDescriptor.bLength
        + sum([len(bytes(x)) for x in descriptor_list])
    ),
    bNumInterfaces=len(interfaces),
)
descriptor_list.insert(0, configuration)

string_descriptors = [
    standard.StringDescriptor(string) for string in StringIndex.strings_in_order()
]
serial_number_descriptor = string_descriptors[SERIAL_NUMBER_INDEX]

c_file = args.output_c_file
h_file = args.output_h_file


c_file.write(
    """\
#include <stdint.h>

#include "tusb.h"
#include "py/objtuple.h"
#include "shared-bindings/usb_hid/Device.h"
#include "{H_FILE_NAME}"

""".format(
        H_FILE_NAME=h_file.name
    )
)

c_file.write(
    """\
// {DESCRIPTION} : {CLASS}
""".format(
        DESCRIPTION=device.description, CLASS=device.__class__
    )
)

c_file.write(
    """\
const uint8_t usb_desc_dev[] = {
"""
)
for b in bytes(device):
    c_file.write("0x{:02x}, ".format(b))

c_file.write(
    """\
};
"""
)

c_file.write(
    """\
const uint8_t usb_desc_cfg[] = {
"""
)

# Write out all the regular descriptors as one long array (that's how ASF4 does it).
descriptor_length = 0
for descriptor in descriptor_list:
    c_file.write(
        """\
// {DESCRIPTION} : {CLASS}
""".format(
            DESCRIPTION=descriptor.description, CLASS=descriptor.__class__
        )
    )

    b = bytes(descriptor)
    notes = descriptor.notes()
    i = 0

    # This prints each subdescriptor on a separate line.
    n = 0
    while i < len(b):
        length = b[i]
        for j in range(length):
            c_file.write("0x{:02x}, ".format(b[i + j]))
        c_file.write("// " + notes[n])
        n += 1
        c_file.write("\n")
        i += length
    descriptor_length += len(b)

c_file.write(
    """\
};
"""
)

pointers_to_strings = []

for idx, descriptor in enumerate(string_descriptors):
    c_file.write(
        """\
// {DESCRIPTION} : {CLASS}
""".format(
            DESCRIPTION=descriptor.description, CLASS=descriptor.__class__
        )
    )

    b = bytes(descriptor)
    notes = descriptor.notes()
    i = 0

    # This prints each subdescriptor on a separate line.
    variable_name = StringIndex.index_to_variable[idx]
    if not variable_name:
        variable_name = "string_descriptor{}".format(idx)
    pointers_to_strings.append("{name}".format(name=variable_name))

    const = "const "
    if variable_name == "usb_serial_number":
        length = len(b)
        c_file.write("    uint16_t {NAME}[{length}];\n".format(NAME=variable_name, length=length//2))
    else:
        c_file.write(
            """\
    const uint16_t {NAME}[] = {{
    """.format(
                const=const, NAME=variable_name
            )
        )
        n = 0
        while i < len(b):
            length = b[i]
            for j in range(length // 2):
                c_file.write("0x{:04x}, ".format(b[i + 2 * j + 1] << 8 | b[i + 2 * j]))
            n += 1
            c_file.write("\n")
            i += length
        c_file.write(
            """\
    };
    """
    )

c_file.write(
    """\
// array of pointer to string descriptors
uint16_t const * const string_desc_arr [] =
{
"""
)
c_file.write(
    """,\

""".join(
        pointers_to_strings
    )
)

c_file.write(
    """
};
"""
)

c_file.write("\n")

if include_hid:
    hid_descriptor_length = len(bytes(combined_hid_report_descriptor))
else:
    hid_descriptor_length = 0

# Now the values we need for the .h file.
h_file.write(
    """\
#ifndef MICROPY_INCLUDED_AUTOGEN_USB_DESCRIPTOR_H
#define MICROPY_INCLUDED_AUTOGEN_USB_DESCRIPTOR_H

#include <stdint.h>

extern const uint8_t usb_desc_dev[{device_length}];
extern const uint8_t usb_desc_cfg[{configuration_length}];
extern uint16_t usb_serial_number[{serial_number_length}];
extern uint16_t const * const string_desc_arr [{string_descriptor_length}];

#define CFG_TUSB_RHPORT0_MODE       ({rhport0_mode})

// Vendor name included in Inquiry response, max 8 bytes
#define CFG_TUD_MSC_VENDOR          "{msc_vendor}"

// Product name included in Inquiry response, max 16 bytes
#define CFG_TUD_MSC_PRODUCT         "{msc_product}"

""".format(
        serial_number_length=len(bytes(serial_number_descriptor)) // 2,
        device_length=len(bytes(device)),
        configuration_length=descriptor_length,
        max_configuration_length=max(hid_descriptor_length, descriptor_length),
        string_descriptor_length=len(pointers_to_strings),
        rhport0_mode="OPT_MODE_DEVICE | OPT_MODE_HIGH_SPEED"
        if args.highspeed
        else "OPT_MODE_DEVICE",
        msc_vendor=args.manufacturer[:8],
        msc_product=args.product[:16],
    )
)

if include_hid:
    h_file.write(
        """\
extern const uint8_t hid_report_descriptor[{hid_report_descriptor_length}];

#define USB_HID_NUM_DEVICES         {hid_num_devices}
""".format(
            hid_report_descriptor_length=len(bytes(combined_hid_report_descriptor)),
            hid_num_devices=len(args.hid_devices),
        )
    )

if include_vendor:
    h_file.write(
        """\
enum
{
  VENDOR_REQUEST_WEBUSB = 1,
  VENDOR_REQUEST_MICROSOFT = 2
};

extern uint8_t const desc_ms_os_20[];

// Currently getting compile-time errors in files like tusb_fifo.c
// if we try do define this here (TODO figure this out!)
//extern const tusb_desc_webusb_url_t desc_webusb_url;

"""
    )

h_file.write(
    """\
#endif // MICROPY_INCLUDED_AUTOGEN_USB_DESCRIPTOR_H
"""
)

if include_hid:
    # Write out the report descriptor and info
    c_file.write(
        """\
const uint8_t hid_report_descriptor[{HID_DESCRIPTOR_LENGTH}] = {{
""".format(
            HID_DESCRIPTOR_LENGTH=hid_descriptor_length
        )
    )

    for b in bytes(combined_hid_report_descriptor):
        c_file.write("0x{:02x}, ".format(b))

    c_file.write(
        """\
};

"""
    )

    # Write out USB HID report buffer definitions.
    for name in args.hid_devices:
        c_file.write(
            """\
static uint8_t {name}_report_buffer[{report_length}];
""".format(
                name=name.lower(),
                report_length=hid_report_descriptors.HID_DEVICE_DATA[
                    name
                ].report_length,
            )
        )

        if hid_report_descriptors.HID_DEVICE_DATA[name].out_report_length > 0:
            c_file.write(
                """\
static uint8_t {name}_out_report_buffer[{report_length}];
""".format(
                    name=name.lower(),
                    report_length=hid_report_descriptors.HID_DEVICE_DATA[
                        name
                    ].out_report_length,
                )
            )

    # Write out table of device objects.
    c_file.write(
        """\
usb_hid_device_obj_t usb_hid_devices[] = {
"""
    )
    for name in args.hid_devices:
        device_data = hid_report_descriptors.HID_DEVICE_DATA[name]
        out_report_buffer = (
            "{}_out_report_buffer".format(name.lower())
            if device_data.out_report_length > 0
            else "NULL"
        )
        c_file.write(
            """\
    {{
        .base          = {{ .type = &usb_hid_device_type }},
        .report_buffer = {name}_report_buffer,
        .report_id     = {report_id},
        .report_length = {report_length},
        .usage_page    = {usage_page:#04x},
        .usage         = {usage:#04x},
        .out_report_buffer = {out_report_buffer},
        .out_report_length = {out_report_length},
    }},
""".format(
                name=name.lower(),
                report_id=report_ids[name],
                report_length=device_data.report_length,
                usage_page=device_data.usage_page,
                usage=device_data.usage,
                out_report_buffer=out_report_buffer,
                out_report_length=device_data.out_report_length,
            )
        )
    c_file.write(
        """\
};
"""
    )

    # Write out tuple of device objects.
    c_file.write(
        """
mp_obj_tuple_t common_hal_usb_hid_devices = {{
    .base = {{
        .type = &mp_type_tuple,
    }},
    .len = {num_devices},
    .items = {{
""".format(
            num_devices=len(args.hid_devices)
        )
    )
    for idx in range(len(args.hid_devices)):
        c_file.write(
            """\
         (mp_obj_t) &usb_hid_devices[{idx}],
""".format(
                idx=idx
            )
        )
    c_file.write(
        """\
    },
};
"""
    )

if include_vendor:
    # Mimic what the tinyusb webusb demo does in its main.c file
    c_file.write(
        """
#define URL   "{webusb_url}"

const tusb_desc_webusb_url_t desc_webusb_url =
{{
  .bLength         = 3 + sizeof(URL) - 1,
  .bDescriptorType = 3, // WEBUSB URL type
  .bScheme         = 1, // 0: http, 1: https, 255: ""
  .url             = URL
}};

// These next two hardcoded descriptors were pulled from the usb_descriptor.c file
// of the tinyusb webusb_serial demo. TODO - this is probably something else to
// integrate into the adafruit_usb_descriptors project...

//--------------------------------------------------------------------+
// BOS Descriptor
//--------------------------------------------------------------------+

/* Microsoft OS 2.0 registry property descriptor
Per MS requirements https://msdn.microsoft.com/en-us/library/windows/hardware/hh450799(v=vs.85).aspx
device should create DeviceInterfaceGUIDs. It can be done by driver and
in case of real PnP solution device should expose MS "Microsoft OS 2.0
registry property descriptor". Such descriptor can insert any record
into Windows registry per device/configuration/interface. In our case it
will insert "DeviceInterfaceGUIDs" multistring property.

GUID is freshly generated and should be OK to use.

https://developers.google.com/web/fundamentals/native-hardware/build-for-webusb/
(Section Microsoft OS compatibility descriptors)
*/

#define BOS_TOTAL_LEN      (TUD_BOS_DESC_LEN + TUD_BOS_WEBUSB_DESC_LEN + TUD_BOS_MICROSOFT_OS_DESC_LEN)

#define MS_OS_20_DESC_LEN  0xB2

// BOS Descriptor is required for webUSB
uint8_t const desc_bos[] =
{{
  // total length, number of device caps
  TUD_BOS_DESCRIPTOR(BOS_TOTAL_LEN, 2),

  // Vendor Code, iLandingPage
  TUD_BOS_WEBUSB_DESCRIPTOR(VENDOR_REQUEST_WEBUSB, 1),

  // Microsoft OS 2.0 descriptor
  TUD_BOS_MS_OS_20_DESCRIPTOR(MS_OS_20_DESC_LEN, VENDOR_REQUEST_MICROSOFT)
}};

uint8_t const * tud_descriptor_bos_cb(void)
{{
  return desc_bos;
}}


#define ITF_NUM_VENDOR   {webusb_interface} // used in this next descriptor

uint8_t const desc_ms_os_20[] =
{{
  // Set header: length, type, windows version, total length
  U16_TO_U8S_LE(0x000A), U16_TO_U8S_LE(MS_OS_20_SET_HEADER_DESCRIPTOR), U32_TO_U8S_LE(0x06030000), U16_TO_U8S_LE(MS_OS_20_DESC_LEN),

  // Configuration subset header: length, type, configuration index, reserved, configuration total length
  U16_TO_U8S_LE(0x0008), U16_TO_U8S_LE(MS_OS_20_SUBSET_HEADER_CONFIGURATION), 0, 0, U16_TO_U8S_LE(MS_OS_20_DESC_LEN-0x0A),

  // Function Subset header: length, type, first interface, reserved, subset length
  U16_TO_U8S_LE(0x0008), U16_TO_U8S_LE(MS_OS_20_SUBSET_HEADER_FUNCTION), ITF_NUM_VENDOR, 0, U16_TO_U8S_LE(MS_OS_20_DESC_LEN-0x0A-0x08),

  // MS OS 2.0 Compatible ID descriptor: length, type, compatible ID, sub compatible ID
  U16_TO_U8S_LE(0x0014), U16_TO_U8S_LE(MS_OS_20_FEATURE_COMPATBLE_ID), 'W', 'I', 'N', 'U', 'S', 'B', 0x00, 0x00,
  0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, // sub-compatible

  // MS OS 2.0 Registry property descriptor: length, type
  U16_TO_U8S_LE(MS_OS_20_DESC_LEN-0x0A-0x08-0x08-0x14), U16_TO_U8S_LE(MS_OS_20_FEATURE_REG_PROPERTY),
  U16_TO_U8S_LE(0x0007), U16_TO_U8S_LE(0x002A), // wPropertyDataType, wPropertyNameLength and PropertyName "DeviceInterfaceGUIDs\0" in UTF-16
  'D', 0x00, 'e', 0x00, 'v', 0x00, 'i', 0x00, 'c', 0x00, 'e', 0x00, 'I', 0x00, 'n', 0x00, 't', 0x00, 'e', 0x00,
  'r', 0x00, 'f', 0x00, 'a', 0x00, 'c', 0x00, 'e', 0x00, 'G', 0x00, 'U', 0x00, 'I', 0x00, 'D', 0x00, 's', 0x00, 0x00, 0x00,
  U16_TO_U8S_LE(0x0050), // wPropertyDataLength
	//bPropertyData: “{{975F44D9-0D08-43FD-8B3E-127CA8AFFF9D}}”.
  '{{', 0x00, '9', 0x00, '7', 0x00, '5', 0x00, 'F', 0x00, '4', 0x00, '4', 0x00, 'D', 0x00, '9', 0x00, '-', 0x00,
  '0', 0x00, 'D', 0x00, '0', 0x00, '8', 0x00, '-', 0x00, '4', 0x00, '3', 0x00, 'F', 0x00, 'D', 0x00, '-', 0x00,
  '8', 0x00, 'B', 0x00, '3', 0x00, 'E', 0x00, '-', 0x00, '1', 0x00, '2', 0x00, '7', 0x00, 'C', 0x00, 'A', 0x00,
  '8', 0x00, 'A', 0x00, 'F', 0x00, 'F', 0x00, 'F', 0x00, '9', 0x00, 'D', 0x00, '}}', 0x00, 0x00, 0x00, 0x00, 0x00
}};

TU_VERIFY_STATIC(sizeof(desc_ms_os_20) == MS_OS_20_DESC_LEN, "Incorrect size");

// End of section about desc_ms_os_20

""".format(
            webusb_url=args.webusb_url,
            webusb_interface=vendor_interface.bInterfaceNumber,
        )
    )
