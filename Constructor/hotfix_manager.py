import unrealsdk
from unrealsdk import *

from . import bl2tools, logging

import os


@logging.log_all_calls(logging.call_logger)
class Hotfixer:

    def __init__(self, path):
        self.PATH = path
        self.definition_files = []
        self.keys = []
        self.values = []
        self.load_files()

    def Enable(self):
        self.merge_files()
        self.execute()
        self.keys.clear()
        self.values.clear()

    def Disable(self):
        pass

    def load_files(self):
        for root, dirs, filenames in os.walk(self.PATH):
            for file in sorted([os.path.join(root, x) for x in filenames]):
                # .definition as alternative suffix support for Exodus
                if file.lower().endswith(".definition") or file.lower().endswith(".blcm"):
                    logging.logger.info(f"Loading: {file}")
                    self.definition_files.append(file)

    def execute(self):
        """
        Executes our merged file
        """
        file = os.path.join(self.PATH, "merge.txt")
        exec_path = str(file).split("Binaries\\", 1)[1]
        bl2tools.console_command("exec " + exec_path, False)
        # Clean up the file
        os.remove(file)

    def merge_files(self):
        SparkServiceConfiguration = None
        set_cmd = "set {} {} ({})\n"
        with open(os.path.join(self.PATH, "merge.txt"), "w", encoding="cp1252") as merge_fp:
            for file in self.definition_files:
                with open(file, "r", encoding="cp1252") as fp:
                    for line in fp:
                        if line.lstrip().lower().startswith("set"):
                            if "SparkService" not in line:
                                merge_fp.write(line)
                            else:
                                _split = line.split(maxsplit=3)
                                attr = _split[2]  # set0 Object1 attribute2 value3:
                                to_merge = _split[3].rstrip()
                                if attr.lower() == "keys":
                                    self.keys.append(to_merge[1:-1])
                                elif attr.lower() == "values":
                                    self.values.append(to_merge[1:-1])

            for x in unrealsdk.FindAll("SparkServiceConfiguration"):
                if x.ServiceName == "Micropatch":
                    SparkServiceConfiguration = x.PathName(x)
                    break
            if not SparkServiceConfiguration:
                SparkServiceConfiguration = "Transient.SparkServiceConfiguration_0"
                merge_fp.write("set Transient.SparkServiceConfiguration_0 ServiceName Micropatch\n")
                merge_fp.write("set Transient.SparkServiceConfiguration_0 ConfigurationGroup Default\n")
                gb_acc = unrealsdk.FindAll("GearboxAccountData")[-1]
                merge_fp.write(
                    "set {} Services (Transient.SparkServiceConfiguration_0)\n".format(gb_acc.PathName(gb_acc)))
            merge_fp.write(set_cmd.format(SparkServiceConfiguration, "Keys", ",".join(self.keys)))
            merge_fp.write(set_cmd.format(SparkServiceConfiguration, "Values", ",".join(self.values)))
