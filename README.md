# **Track-Unmix: Music Separation as a Service (MSaaS)**

Track-Unmix provides an automated music separation service deployed on Kubernetes. It leverages Facebook's **Demucs** for waveform source separation and a microservices architecture to process, analyze, and retrieve separated audio tracks.

---

## **Overview**
Track-Unmix enables efficient processing of MP3 files by separating audio into distinct tracks (vocals, instruments, etc.) using a **REST API**. The system queues requests via Redis, processes them using dedicated workers, and stores the results in a cloud object store.

---

## **Architecture**
The project employs a **microservices-based Kubernetes deployment** with the following components:
1. **REST Service**: Handles API requests and queues jobs in Redis.
2. **Worker Nodes**: Process MP3 files using **Demucs** and store results in an object store.
3. **Redis**: Serves as a message queue for task management.
4. **Min.io (or Object Store)**: Stores original and processed audio files.

---

## **Features**
- **Scalable Architecture**: Kubernetes deployment enables horizontal scaling for workers.
- **Waveform Separation**: Uses Demucs for high-quality audio separation.
- **Cloud Object Storage**: Stores MP3 files and processed outputs for retrieval.
- **Development and Deployment**: Supports both local and cloud (GKE) setups.

---

## **Setup and Deployment**

### **Prerequisites**
- **Docker**: Build and run containers.
- **Kubernetes**: Deploy microservices locally or on GKE.
- **Min.io**: For object storage.

### **Setup Steps**
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd track-unmix
   ```

2. Deploy Redis and Min.io locally using `deploy-local-dev.sh`:
   ```bash
   ./deploy-local-dev.sh
   ```

3. Build and push container images:
   ```bash
   docker build -t <image-name>:<version> .
   docker push <image-name>:<version>
   ```

4. Deploy to Kubernetes:
   - Deploy Redis and Min.io services as per `redis/README.md` and `worker/README.md`.
   - Deploy REST and worker services.

5. Enable port-forwarding for local development:
   ```bash
   kubectl port-forward service/redis 6379:6379 &
   kubectl port-forward --namespace minio-ns svc/myminio-proj 9000:9000 &
   ```

## **Components**

### **1. REST Service**
- Accepts API requests for audio processing.
- Queues tasks in Redis for worker processing.
- API Documentation in `rest/README.md`.

### **2. Worker Nodes**
- Processes MP3 files using **Demucs**.
- Stores separated tracks in Min.io (or any compatible object storage).
- Details in `worker/README.md`.

### **3. Redis**
- Serves as the task queue using Redis list operations (`lpush`, `blpop`).
- Managed by `redis/README.md`.

### **4. Object Storage (Min.io)**
- Stores original MP3s and processed output.
- Sample buckets:
  - **queue**: For input MP3 files.
  - **output**: For separated audio tracks (e.g., `<songhash>-vocals.mp3`).
- Min.io setup in `redis/README.md`.


## **Workflow**
1. Send an MP3 file for processing via the REST API.
2. REST service queues the job in Redis.
3. Worker node fetches the job, processes it with **Demucs**, and stores the output in the object store.
4. Retrieve separated tracks from the output bucket.

---

## **Note**
- **Demucs Resource Requirement**: Requires 6GB+ memory for audio separation.
- **Versioning**: Use version tags for Docker images to avoid conflicts during development.
- **Cloud Setup**: Transition to GKE after testing locally.