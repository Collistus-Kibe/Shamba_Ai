const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000/api/v1";

class ApiService {
  private getHeaders(): HeadersInit {
    const headers: HeadersInit = {};
    const token = localStorage.getItem("shamba_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    return headers;
  }

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
      ...this.getHeaders(),
      ...(options.headers || {}),
    };

    const config = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      if (response.status === 401) {
        // Clear token if unauthorized
        localStorage.removeItem("shamba_token");
        localStorage.removeItem("shamba_user");
        window.dispatchEvent(new Event("auth-changed"));
      }

      if (!response.ok) {
        const errText = await response.text();
        let errMsg = "API Request failed";
        try {
          const parsed = JSON.parse(errText);
          errMsg = parsed.detail || parsed.message || errMsg;
        } catch {
          errMsg = errText || errMsg;
        }
        throw new Error(errMsg);
      }

      if (response.status === 204) {
        return null as unknown as T;
      }

      return (await response.json()) as T;
    } catch (e: any) {
      console.error(`Fetch error on endpoint ${endpoint}:`, e);
      throw e;
    }
  }

  // --- AUTH ENDPOINTS ---

  async register(email: string, password: string, fullName?: string): Promise<any> {
    const data = await this.request<any>("/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    return data;
  }

  async login(email: string, password: string): Promise<any> {
    // Form encoded login structure for OAuth2PasswordRequestForm
    const formData = new URLSearchParams();
    formData.append("username", email);
    formData.append("password", password);

    const data = await this.request<any>("/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body: formData.toString(),
    });
    
    if (data.access_token) {
      localStorage.setItem("shamba_token", data.access_token);
      localStorage.setItem("shamba_user", JSON.stringify(data.user));
      window.dispatchEvent(new Event("auth-changed"));
    }
    return data;
  }

  async loginGoogle(credential: string): Promise<any> {
    const data = await this.request<any>("/auth/google", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ credential }),
    });
    if (data.access_token) {
      localStorage.setItem("shamba_token", data.access_token);
      localStorage.setItem("shamba_user", JSON.stringify(data.user));
      window.dispatchEvent(new Event("auth-changed"));
    }
    return data;
  }

  async loginFirebase(idToken: string, fullName?: string): Promise<any> {
    const data = await this.request<any>("/auth/firebase", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ id_token: idToken, full_name: fullName }),
    });
    if (data.access_token) {
      localStorage.setItem("shamba_token", data.access_token);
      localStorage.setItem("shamba_user", JSON.stringify(data.user));
      window.dispatchEvent(new Event("auth-changed"));
    }
    return data;
  }

  logout(): void {
    localStorage.removeItem("shamba_token");
    localStorage.removeItem("shamba_user");
    window.dispatchEvent(new Event("auth-changed"));
  }

  async getMe(): Promise<any> {
    return this.request<any>("/auth/me");
  }

  // --- FARM ENDPOINTS ---

  async getFarms(): Promise<any[]> {
    return this.request<any[]>("/farms/");
  }

  async createFarm(farm: {
    name: string;
    crop_type: string;
    latitude?: number;
    longitude?: number;
    boundary?: any;
    area_hectares?: number;
  }): Promise<any> {
    return this.request<any>("/farms/", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(farm),
    });
  }

  async getFarmCrops(farmId: number): Promise<any[]> {
    return this.request<any[]>(`/farms/${farmId}/crops`);
  }

  async createFarmCrop(farmId: number, crop: { crop_name: string; variety?: string; planting_date?: string }): Promise<any> {
    return this.request<any>(`/farms/${farmId}/crops`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(crop),
    });
  }

  // --- ASSISTANT ENDPOINTS ---

  async getConversations(): Promise<any[]> {
    return this.request<any[]>("/assistant/conversations");
  }

  async createConversation(title: string, farmId?: number): Promise<any> {
    return this.request<any>("/assistant/conversations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, farm_id: farmId }),
    });
  }

  async getConversationDetails(convId: number): Promise<any> {
    return this.request<any>(`/assistant/conversations/${convId}`);
  }

  async postChatMessage(convId: number, text: string): Promise<any> {
    return this.request<any>(`/assistant/conversations/${convId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message_text: text }),
    });
  }

  async transcribeAudio(audioFile: File): Promise<{ text: string }> {
    const formData = new FormData();
    formData.append("audio", audioFile);
    return this.request<{ text: string }>("/assistant/transcribe", {
      method: "POST",
      body: formData,
    });
  }

  // --- DISEASE DIAGNOSIS ENDPOINTS ---

  async diagnoseCropImage(imageFile: File, cropType?: string, farmId?: number): Promise<any> {
    const formData = new FormData();
    formData.append("image", imageFile);
    if (cropType) formData.append("crop_type", cropType);
    if (farmId) formData.append("farm_id", farmId.toString());

    return this.request<any>("/diseases/diagnose", {
      method: "POST",
      body: formData,
    });
  }

  async getDiseaseReports(farmId?: number): Promise<any[]> {
    const endpoint = farmId ? `/diseases/reports?farm_id=${farmId}` : "/diseases/reports";
    return this.request<any[]>(endpoint);
  }

  async getDiseaseReportDetails(reportId: number): Promise<any> {
    return this.request<any>(`/diseases/reports/${reportId}`);
  }

  // --- WEATHER ENDPOINTS ---

  async getFarmWeather(farmId: number): Promise<any> {
    return this.request<any>(`/weather/farms/${farmId}/weather`);
  }

  async getFarmWeatherHistory(farmId: number): Promise<any[]> {
    return this.request<any[]>(`/weather/farms/${farmId}/weather/history`);
  }

  // --- MARKET ENDPOINTS ---

  async getMarketPrices(crop?: string, region?: string): Promise<any[]> {
    let query = "";
    const params = new URLSearchParams();
    if (crop) params.append("crop", crop);
    if (region) params.append("region", region);
    if (params.toString()) {
      query = `?${params.toString()}`;
    }
    return this.request<any[]>(`/market/prices${query}`);
  }

  async getMarketCrops(): Promise<string[]> {
    return this.request<string[]>("/market/crops");
  }

  async getMarketBest(crop: string): Promise<any> {
    return this.request<any>(`/market/best-market?crop=${encodeURIComponent(crop)}`);
  }

  // --- NOTIFICATION ENDPOINTS ---

  async getNotifications(): Promise<any[]> {
    return this.request<any[]>("/notifications/");
  }

  async markRead(notifId: number): Promise<any> {
    return this.request<any>(`/notifications/${notifId}/read`, {
      method: "PUT",
    });
  }

  async markAllRead(): Promise<any[]> {
    return this.request<any[]>("/notifications/read-all", {
      method: "PUT",
    });
  }
}

export const api = new ApiService();
export default api;
