import 'package:flutter/material.dart';
import 'package:webview_flutter/webview_flutter.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  runApp(MyApp());
}

class MyApp extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      home: OrderPage(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class OrderPage extends StatefulWidget {
  @override
  _OrderPageState createState() => _OrderPageState();
}

class _OrderPageState extends State<OrderPage> {
  final TextEditingController urlController = TextEditingController();
  late WebViewController webController;

  String currentUrl = "http://127.0.0.1/app/index.php";

  @override
  void initState() {
    super.initState();
    loadUrl();
  }

  Future<void> loadUrl() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    setState(() {
      currentUrl = prefs.getString("order_url") ?? currentUrl;
      urlController.text = currentUrl;
    });

    webController = WebViewController()
      ..setJavaScriptMode(JavaScriptMode.unrestricted)
      ..loadRequest(Uri.parse(currentUrl));
  }

  Future<void> saveUrl() async {
    SharedPreferences prefs = await SharedPreferences.getInstance();
    await prefs.setString("order_url", urlController.text);

    setState(() {
      currentUrl = urlController.text;
    });

    webController.loadRequest(Uri.parse(currentUrl));
    Navigator.pop(context);
  }

  void openSettings() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text("Server Settings"),
        content: TextField(
          controller: urlController,
          decoration: InputDecoration(
            hintText: "http://192.168.1.5:5000",
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text("Cancel"),
          ),
          ElevatedButton(
            onPressed: saveUrl,
            child: Text("Save"),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text("🍔 Snack in Save 9Nueve"),
        backgroundColor: Colors.deepOrange,
        actions: [
          IconButton(
            icon: Icon(Icons.settings),
            onPressed: openSettings,
          )
        ],
      ),
      body: WebViewWidget(controller: webController),
    );
  }
}