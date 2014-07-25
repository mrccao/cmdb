from models import L2Domain, L3Domain, System, Vendor, HardwareModel, Hardware, SystemCategory, County, Country, HardwareType, Software, SoftwareVersion, City, Street, Location

navbar = dict()
navbar["Organization"] = (Vendor,)
navbar["Domain"] = (L2Domain, L3Domain)
navbar["System"] = (System, SystemCategory)
navbar["Hardware"] = (Hardware, HardwareModel, HardwareType)
navbar["Software"] = (Software, SoftwareVersion)
navbar["Location"] = (Country, County, City, Street, Location)

