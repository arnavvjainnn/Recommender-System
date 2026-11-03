using System;
using System.IO;
using System.Net;
using System.Text;
using System.Threading;

namespace RecommendAIServer
{
    class Program
    {
        private static HttpListener _listener;
        private static string _baseDir;

        static void Main(string[] args)
        {
            _baseDir = AppDomain.CurrentDomain.BaseDirectory;
            int port = 8000;
            int customPort;
            if (args.Length > 0 && int.TryParse(args[0], out customPort))
            {
                port = customPort;
            }

            _listener = new HttpListener();
            _listener.Prefixes.Add("http://localhost:" + port + "/");
            _listener.Prefixes.Add("http://127.0.0.1:" + port + "/");

            try
            {
                _listener.Start();
                Console.WriteLine("RecommendAI Web Server LIVE on http://localhost:" + port + "/");
                _listener.BeginGetContext(OnContextReceived, null);

                // Keep process alive
                Thread.Sleep(Timeout.Infinite);
            }
            catch (Exception ex)
            {
                Console.WriteLine("Server error: " + ex.Message);
            }
        }

        private static void OnContextReceived(IAsyncResult ar)
        {
            try
            {
                if (!_listener.IsListening) return;
                HttpListenerContext context = _listener.EndGetContext(ar);
                // Immediately listen for next request
                _listener.BeginGetContext(OnContextReceived, null);

                // Handle request asynchronously on thread pool
                ThreadPool.QueueUserWorkItem((state) => ProcessRequest(context));
            }
            catch (Exception ex)
            {
                // listener may have stopped
            }
        }

        private static void ProcessRequest(HttpListenerContext context)
        {
            try
            {
                HttpListenerRequest request = context.Request;
                HttpListenerResponse response = context.Response;

                string rawUrl = request.Url.AbsolutePath;
                if (string.IsNullOrEmpty(rawUrl) || rawUrl == "/")
                {
                    rawUrl = "/index.html";
                }

                string relativePath = rawUrl.TrimStart('/').Replace('/', Path.DirectorySeparatorChar);
                string filePath = Path.Combine(_baseDir, relativePath);

                if (File.Exists(filePath))
                {
                    byte[] data = File.ReadAllBytes(filePath);
                    response.ContentType = GetMimeType(Path.GetExtension(filePath));
                    response.ContentLength64 = data.Length;
                    response.AddHeader("Access-Control-Allow-Origin", "*");
                    response.AddHeader("Cache-Control", "no-cache");
                    response.StatusCode = (int)HttpStatusCode.OK;
                    response.OutputStream.Write(data, 0, data.Length);
                }
                else
                {
                    response.StatusCode = (int)HttpStatusCode.NotFound;
                    byte[] notFound = Encoding.UTF8.GetBytes("404 Not Found");
                    response.OutputStream.Write(notFound, 0, notFound.Length);
                }

                response.OutputStream.Close();
            }
            catch
            {
                try { context.Response.Close(); } catch { }
            }
        }

        private static string GetMimeType(string extension)
        {
            if (string.IsNullOrEmpty(extension)) return "application/octet-stream";
            switch (extension.ToLower())
            {
                case ".html": case ".htm": return "text/html; charset=utf-8";
                case ".js": return "application/javascript; charset=utf-8";
                case ".css": return "text/css; charset=utf-8";
                case ".json": return "application/json; charset=utf-8";
                case ".png": return "image/png";
                case ".jpg": case ".jpeg": return "image/jpeg";
                case ".svg": return "image/svg+xml";
                case ".ico": return "image/x-icon";
                default: return "application/octet-stream";
            }
        }
    }
}
