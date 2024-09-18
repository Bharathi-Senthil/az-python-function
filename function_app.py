import azure.functions as func
import logging
import requests
from multiprocessing import Process,Queue
app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


def httpCall(url: str, queue: Queue):
    try:
        response = requests.get(url)
        queue.put(response)
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP request failed: {e}")
        queue.put(None)

@app.route(route="main")
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            logging.info('Trying to get JSON body')
            req_body = req.get_json()


            response1 = httpCall("http://localhost:7071/api/worker1?name=worker1")
            response2 = httpCall("http://localhost:7071/api/worker2?name=worker2")

            logging.info(f"Response code: {response1.status_code}")
            logging.info(f"Response code: {response2.status_code}")
            
            if response1.status_code == 200 and response2.status_code == 200:
                data1 = response1.content  # Parse JSON data from the response
                data2 = response2.content  # Parse JSON data from the response
                logging.info(f"Response from worker1: {data1} , Response from worker2: {data2}")
            else:
                logging.error(f"Error: {response1.status_code}, Response: {response1.text}")
                return func.HttpResponse(f"Failed to trigger worker1: {response1.status_code}", status_code=response1.status_code)

        except ValueError as ve:
            logging.error(f"Error parsing JSON body: {ve}")
            return func.HttpResponse("Invalid JSON body", status_code=400)

    if name:
        return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    else:
        return func.HttpResponse(
            "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
            status_code=200
        )


@app.route(route="multiprocessing", auth_level=func.AuthLevel.FUNCTION)
def mutliprocess(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Multiprocessing HTTP trigger function processed a request.')

    queue = Queue()
    try:
        p1 = Process(target=httpCall, args=("http://localhost:7071/api/worker1?name=worker1", queue))
        p2 = Process(target=httpCall, args=("http://localhost:7071/api/worker2?name=worker2", queue))
        
        p1.start()
        p2.start()

        p1.join()
        p2.join()

        response1 = queue.get()
        response2 = queue.get()

        if response1 and response1.status_code == 200:
            data1 = response1.content
            logging.info(f"Response from worker1: {data1}")
        else:
            logging.error(f"Error calling worker1: {response1.status_code if response1 else 'No response'}")
            return func.HttpResponse("Failed to trigger worker1", status_code=500)

        if response2 and response2.status_code == 200:
            data2 = response2.content
            logging.info(f"Response from worker2: {data2}")
        else:
            logging.error(f"Error calling worker2: {response2.status_code if response2 else 'No response'}")
            return func.HttpResponse("Failed to trigger worker2", status_code=500)

        return func.HttpResponse("All processes are done!", status_code=200)
    except Exception as e:
        logging.error(f"Error: {e}")
        return func.HttpResponse(f"Error: {e}", status_code=500)




@app.route(route="worker1", auth_level=func.AuthLevel.FUNCTION)
def worker1(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Worker1 HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
            name = req_body.get('name')
        except ValueError:
            name = None

    if name:
        logging.info(f"Worker1 executed successfully with name: {name}")
        return func.HttpResponse(f"Hello, {name}. Worker1 executed successfully.")
    else:
        logging.warning("Worker1 executed without a name.")
        return func.HttpResponse(
            "Worker1 executed successfully. Pass a name in the query string or in the request body for a personalized response.",
            status_code=200
        )



@app.route(route="worker2", auth_level=func.AuthLevel.FUNCTION)
def worker2(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Worker2 HTTP trigger function processed a request.')

    name = req.params.get('name')
    if not name:
        try:
            req_body = req.get_json()
            name = req_body.get('name')
        except ValueError:
            name = None

    if name:
        logging.info(f"Worker2 executed successfully with name: {name}")
        return func.HttpResponse(f"Hello, {name}. Worker2 executed successfully.")
    else:
        logging.warning("Worker2 executed without a name.")
        return func.HttpResponse(
            "Worker2 executed successfully. Pass a name in the query string or in the request body for a personalized response.",
            status_code=200
        )
