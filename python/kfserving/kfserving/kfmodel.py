# Copyright 2020 kubeflow.org.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Dict
import sys

import json
import tornado.web
from tornado.httpclient import AsyncHTTPClient

PREDICTOR_URL_FORMAT = "http://{0}/v1/models/{1}:predict"
EXPLAINER_URL_FORMAT = "http://{0}/v1/models/{1}:explain"


# KFModel is intended to be subclassed by various components within KFServing.
class KFModel:

    def __init__(self, name: str):
        self.name = name
        self.ready = False
        self.predictor_host = None
        self.explainer_host = None
        # The timeout matches what is set in generated Istio resorurces.
        # We generally don't want things to time out at the request level here,
        # timeouts should be handled elsewhere in the system.
        self.timeout = 600
        self._http_client_instance = None

    @property
    def _http_client(self):
        if self._http_client_instance is None:
            self._http_client_instance = AsyncHTTPClient(max_clients=sys.maxsize)
        return self._http_client_instance

    def load(self) -> bool:
        self.ready = True
        return self.ready

    def preprocess(self, request: Dict) -> Dict:
        return request

    def postprocess(self, request: Dict) -> Dict:
        return request

    async def predict(self, request: Dict) -> Dict:
        if not self.predictor_host:
            raise NotImplementedError

        response = await self._http_client.fetch(
            PREDICTOR_URL_FORMAT.format(self.predictor_host, self.name),
            method='POST',
            request_timeout=self.timeout,
            body=json.dumps(request)
        )
        if response.code != 200:
            raise tornado.web.HTTPError(
                status_code=response.code,
                reason=response.body)
        return json.loads(response.body)

    async def explain(self, request: Dict) -> Dict:
        if self.explainer_host is None:
            raise NotImplementedError

        response = await self._http_client.fetch(
            url=EXPLAINER_URL_FORMAT.format(self.explainer_host, self.name),
            method='POST',
            request_timeout=self.timeout,
            body=json.dumps(request)
        )
        if response.code != 200:
            raise tornado.web.HTTPError(
                status_code=response.code,
                reason=response.body)
        return json.loads(response.body)
