import requests

class MetarData:
    def __init__(self, station_code):
        self.station_code = station_code.upper()
        self.url = f"http://tgftp.nws.noaa.gov/data/observations/metar/stations/{station_code}.TXT"
        self.timestamp = None
        self.report = None
        self.error = None

    ## Mengambil data METAR dari API NOAA dan melakukan parsing lebih detail
    def fetch_data(self):
        """Mengambil data METAR dari API NOAA"""
        try:
            response = requests.get(self.url)
            if response.status_code == 200:
                data_lines = response.text.strip().split('\n')
                if len(data_lines) >= 2:
                    self.timestamp = data_lines[0]
                    self.report = data_lines[1]
                else:
                    self.error = "Format data METAR tidak sesuai. (4 Digit Kode Stasiun dan Laporan METAR)"
            else:
                self.error = f"Gagal mengambil data METAR untuk stasiun {self.station_code}. Pastikan kode stasiun benar."
        except requests.exceptions.RequestException as e:
            self.error = f"Terjadi kesalahan saat mengambil data: {e}"

    ## Parsing lebih detail data METAR untuk menampilkan penjelasan
    def parse_metar(self):
        """Parsing lebih detail data METAR dengan penjelasan singkatan"""
        if self.report is None:
            return None

        parsed_data = {
            "wind": {"value": None, "description": None},
            "visibility": {"value": None, "description": None},
            "weather": {"value": None, "description": None},
            "clouds": {"value": [], "description": []},
            "temperature": {"value": None, "description": None},
            "dew_point": {"value": None, "description": None},
            "pressure": {"value": None, "description": None},
            "remarks": {"value": None, "description": None}
        }

        ## Memecah Bagian Metar
        metar_parts = self.report.split()
        index = 0

        # Parsing kode stasiun dan waktu
        if index < len(metar_parts) and metar_parts[index].startswith(self.station_code):
            index += 1
        if index < len(metar_parts) and metar_parts[index].endswith("Z"):
            index += 1

        # Parsing angin (contoh: 19004KT)
        if index < len(metar_parts) and metar_parts[index].endswith("KT"):
            wind = metar_parts[index]
            parsed_data["wind"]["value"] = wind
            direction = wind[:3] if wind != "VRB" else "Variable"
            speed = wind[3:5] + " knots"
            parsed_data["wind"]["description"] = f"Wind direction {direction} degrees, speed {speed}"
            index += 1

        # Parsing visibilitas (contoh: 9999)
        if index < len(metar_parts) and (metar_parts[index].isdigit() or metar_parts[index] == "9999"):
            visibility = metar_parts[index]
            parsed_data["visibility"]["value"] = f"{visibility} meter"
            parsed_data["visibility"]["description"] = f"Visibility {visibility} meter{' (10 km or more)' if visibility == '9999' else ''}"
            index += 1

        # Parsing kondisi cuaca (contoh: TS, -RA)
        weather_codes = []
        weather_desc = []
        weather_dict = {
            "TS": "Thunderstorm", "RA": "Rain", "SHRA": "Rain showers", "DZ": "Drizzle",
            "BR": "Mist", "FG": "Fog", "HZ": "Haze", "+": "Heavy", "-": "Light", "VC": "In the vicinity"
        }
        while index < len(metar_parts) and (metar_parts[index].startswith(("+", "-", "VC")) or metar_parts[index] in weather_dict):
            code = metar_parts[index]
            desc = []
            if code.startswith("+"):
                desc.append(weather_dict["+"])
                code = code[1:]
            elif code.startswith("-"):
                desc.append(weather_dict["-"])
                code = code[1:]
            elif code.startswith("VC"):
                desc.append(weather_dict["VC"])
                code = code[2:]
            desc.append(weather_dict.get(code, code))
            weather_codes.append(metar_parts[index])
            weather_desc.append(" ".join(desc))
            index += 1
        if weather_codes:
            parsed_data["weather"]["value"] = " ".join(weather_codes)
            parsed_data["weather"]["description"] = ", ".join(weather_desc)

        # Parsing awan (contoh: FEW017, BKN018, SKC, CLR)
        cloud_dict = {
            "FEW": "Few clouds (1-2 oktas, less than 25% sky coverage)",
            "SCT": "Scattered clouds (3-4 oktas, 25-50% sky coverage)",
            "BKN": "Broken clouds (5-7 oktas, 51-87% sky coverage)",
            "OVC": "Overcast (8 oktas, 88-100% sky coverage)",
            "SKC": "Sky clear (no clouds observed)",
            "CLR": "Clear below 12,000 feet (no clouds below 12,000 feet AGL)"
        }
        cloud_types = {
            "CB": "Cumulonimbus (thunderstorm clouds, often associated with heavy rain or storms)",
            "TCU": "Towering Cumulus (large cumulus clouds with potential to develop into cumulonimbus)"
        }
        while index < len(metar_parts) and (metar_parts[index] in cloud_dict or metar_parts[index].startswith(("FEW", "SCT", "BKN", "OVC"))):
            cloud_layer = metar_parts[index]
            if cloud_layer in ["SKC", "CLR"]:
                parsed_data["clouds"]["value"].append(cloud_layer)
                parsed_data["clouds"]["description"].append(cloud_dict[cloud_layer])
                index += 1
                continue
            cloud_type = cloud_dict[cloud_layer[:3]]
            cloud_height = int(cloud_layer[3:6]) * 100  # Tinggi dalam kaki (feet)
            cloud_height_meters = int(cloud_height * 0.3048)  # Konversi ke meter (lebih umum di indo)
            cloud_extra = ""
            cloud_extra_desc = ""
            if index + 1 < len(metar_parts) and metar_parts[index + 1].startswith(("CB", "TCU")):
                cloud_extra = f" ({metar_parts[index + 1]})"
                cloud_extra_desc = f", type: {cloud_types[metar_parts[index + 1]]}"
                index += 1
            parsed_data["clouds"]["value"].append(cloud_layer + cloud_extra)
            parsed_data["clouds"]["description"].append(
                f"{cloud_type}, height {cloud_height} feet ({cloud_height_meters} meters) above ground level{cloud_extra_desc}"
            )
            index += 1

        # Parsing suhu dan titik embun (contoh: 29/28)
        if index < len(metar_parts) and '/' in metar_parts[index]:
            temp_dew = metar_parts[index].split('/')
            parsed_data["temperature"]["value"] = temp_dew[0] + "°C"
            parsed_data["dew_point"]["value"] = temp_dew[1] + "°C"
            parsed_data["temperature"]["description"] = f"Temperature {temp_dew[0]} degrees Celsius"
            parsed_data["dew_point"]["description"] = f"Dew point {temp_dew[1]} degrees Celsius"
            index += 1

        # Parsing tekanan (contoh: Q1009)
        if index < len(metar_parts) and metar_parts[index].startswith("Q"):
            pressure = metar_parts[index]
            parsed_data["pressure"]["value"] = pressure
            parsed_data["pressure"]["description"] = f"Pressure {pressure[1:]} hPa"
            index += 1

        # Parsing remarks (contoh: NOSIG atau lainnya)
        remarks_dict = {"NOSIG": "No significant change expected"}
        if index < len(metar_parts):
            remarks = " ".join(metar_parts[index:])
            parsed_data["remarks"]["value"] = remarks
            parsed_data["remarks"]["description"] = remarks_dict.get(remarks, remarks)
            index += 1

        return parsed_data

    # Mengembalikan data METAR dan error jika ada
    def get_data(self):
        """Mengembalikan data METAR dan error jika ada"""
        return {
            "timestamp": self.timestamp,
            "report": self.report,
            "parsed": self.parse_metar(),
            "error": self.error
        }