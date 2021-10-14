import base64
import logging
import tempfile
from typing import List

from pydantic import BaseSettings

from model.instance import Instance
from model.prediction import Prediction
from mmda.parsers.symbol_scraper_parser import (
    SymbolScraperParser,
    logger as symbol_scraper_parser_logger,
)
from mmda.rasterizers.rasterizer import Rasterizer


class PredictorConfig(BaseSettings):
    """
    The set of configuration parameters required to instantiate a predictor and
    initialize it for inference. This is an appropriate place to specify any parameter
    or configuration values your model requires that aren't packaged with your
    versioned model artifacts. These should be rare beyond the included
    `artifacts_dir`.

    Values for these config fields can be provided as environment variables, see:
    `./docker.env`
    """

    pass


class Predictor:
    """
    Used by the included FastAPI server to perform inference. Initialize your model
    in the constructor using the supplied `PredictorConfig` instance, and perform inference
    for each `Instance` passed via `predict_batch()`. The default batch size is `1`, but
    you should handle as many `Instance`s as are provided.
    """

    _config: PredictorConfig

    def __init__(self, config: PredictorConfig):
        """
        Initialize your model using the passed parameters
        """
        self._config = config
        self._sscraper = SymbolScraperParser(sscraper_bin_path="sscraper")
        symbol_scraper_parser_logger.setLevel(logging.ERROR)
        self._rasterizer = Rasterizer()

    def predict(self, instance: Instance) -> Prediction:
        with tempfile.TemporaryDirectory() as tempdir:
            pdf_path = f"{tempdir}/input.pdf"
            with open(pdf_path, "wb") as f:
                f.write(base64.b64decode(instance.pdf))
            doc = self._sscraper.parse(input_pdf_path=pdf_path)
            images = self._rasterizer.rasterize(input_pdf_path=pdf_path, dpi=200)    # TODO <<
            doc.images = images
            return Prediction(**doc.to_json(with_images=True))

    def predict_batch(self, instances: List[Instance]) -> List[Prediction]:
        return [self.predict(instance) for instance in instances]
