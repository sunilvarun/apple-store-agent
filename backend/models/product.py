from pydantic import BaseModel


class StorageTier(BaseModel):
    capacity: str
    price_usd: int


class CameraSpec(BaseModel):
    label: str
    megapixels: int
    aperture: str
    ois: bool = False
    focal_length_mm: int = 0
    autofocus: bool = False


class IPhoneProduct(BaseModel):
    model_slug: str
    display_name: str
    series: str
    tier: str                        # "pro" | "standard"
    chip: str
    display_size: float
    display_type: str
    display_resolution: str
    display_brightness_nits: int
    storage_tiers: list[StorageTier]
    starting_price: int
    rear_cameras: list[CameraSpec]
    front_camera: CameraSpec
    max_optical_zoom: str
    max_digital_zoom: str
    video_max: str
    battery_hours_video: int
    battery_hours_audio: int
    water_resistance: str
    height_mm: float
    width_mm: float
    depth_mm: float
    weight_grams: int
    connector: str
    biometrics: str
    five_g: bool
    wifi: str
    magsafe: bool
    satellite_sos: bool
    apple_intelligence: bool
    colors: list[str]
    image_url: str
    specs_url: str
