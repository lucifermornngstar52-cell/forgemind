"""Forgemind APK Builder — self-packaging into an Android app.

Generates a minimal Flutter project that wraps Forgemind's core,
pushes it to GitHub, and triggers a CI build to produce an APK.
"""

import os
import json
import subprocess
from pathlib import Path
from rich.console import Console

console = Console()

# Flutter project template — minimal dark-themed Forgemind mobile app
FLUTTER_MAIN = r'''import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

void main() => runApp(const ForgemindApp());

class ForgemindApp extends StatelessWidget {
  const ForgemindApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Forgemind',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        brightness: Brightness.dark,
        scaffoldBackgroundColor: const Color(0xFF0A0A0F),
        colorScheme: const ColorScheme.dark(
          primary: Color(0xFF6C5CE7),
          secondary: Color(0xFF00CEC9),
          surface: Color(0xFF15151F),
        ),
      ),
      home: const ForgemindHome(),
    );
  }
}

class ForgemindHome extends StatefulWidget {
  const ForgemindHome({super.key});
  @override State<ForgemindHome> createState() => _ForgemindHomeState();
}

class _ForgemindHomeState extends State<ForgemindHome> {
  final List<String> _log = [];
  bool _running = false;
  String _status = 'Idle';

  Future<void> _runCycle() async {
    setState(() {
      _running = true;
      _status = 'Forging...';
      _log.insert(0, '> Starting self-improvement cycle...');
    });

    try {
      // Forgemind runs locally via platform channel or HTTP
      final response = await http.post(
        Uri.parse('https://forgemind-bot-hehb.onrender.com/cycle'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 20));

      final result = json.decode(response.body);
      setState(() {
        _status = 'Complete';
        _log.insert(0, '> Improvements: ${result["improvements"]}');
        _log.insert(0, '> Success rate: ${result["success_rate"]}');
        _log.insert(0, '> Iterations: ${result["iterations"]}');
        _log.insert(0, '> Cycle complete.');
      });
    } catch (e) {
      setState(() {
        _status = 'Offline — running in standalone mode';
        _log.insert(0, '> Forgemind core not reachable. APK runs in display mode.');
        _log.insert(0, '> Connect to Forgemind server for live cycles.');
      });
    } finally {
      setState(() => _running = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Row(children: [
          Icon(Icons.precision_manufacturing, color: Color(0xFF6C5CE7)),
          SizedBox(width: 8),
          Text('FORGEMIND', style: TextStyle(fontWeight: FontWeight.bold, letterSpacing: 2)),
        ]),
        actions: [
          Padding(
            padding: const EdgeInsets.only(right: 16),
            child: Center(
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                decoration: BoxDecoration(
                  color: _running ? const Color(0xFF00CEC9).withOpacity(0.2) : const Color(0xFF15151F),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(_status, style: TextStyle(
                  fontSize: 12,
                  color: _running ? const Color(0xFF00CEC9) : Colors.white54,
                )),
              ),
            ),
          ),
        ],
      ),
      body: Column(children: [
        Expanded(
          child: _log.isEmpty
              ? const Center(child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Icon(Icons.precision_manufacturing, size: 64, color: Color(0xFF6C5CE7)),
                    SizedBox(height: 16),
                    Text('The mind that forges itself',
                      style: TextStyle(color: Colors.white54, fontSize: 16)),
                    SizedBox(height: 8),
                    Text('Press FORGE to begin', style: TextStyle(color: Colors.white30, fontSize: 13)),
                  ],
                ))
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _log.length,
                  itemBuilder: (ctx, i) => Padding(
                    padding: const EdgeInsets.only(bottom: 6),
                    child: Text(_log[i],
                      style: const TextStyle(color: Colors.white70, fontFamily: 'monospace', fontSize: 13)),
                  ),
                ),
        ),
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 8, 16, 32),
          child: SizedBox(
            width: double.infinity,
            height: 56,
            child: ElevatedButton.icon(
              onPressed: _running ? null : _runCycle,
              icon: _running
                  ? const SizedBox(width: 20, height: 20,
                      child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                  : const Icon(Icons.whatshot, size: 24),
              label: Text(
                _running ? 'FORGING...' : 'FORGE',
                style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold, letterSpacing: 2),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF6C5CE7),
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
              ),
            ),
          ),
        ),
      ]),
    );
  }
}
'''

GITHUB_ACTIONS = r'''name: Build Forgemind APK

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with:
          channel: stable
      - run: flutter pub get
      - run: flutter build apk --release
      - uses: actions/upload-artifact@v4
        with:
          name: forgemind-apk
          path: build/app/outputs/flutter-apk/app-release.apk
'''

PUBSPEC = r'''name: forgemind
description: Forgemind — The mind that forges itself
version: 1.0.0+1

environment:
  sdk: ">=3.3.0 <4.0.0"

dependencies:
  flutter:
    sdk: flutter
  http: ^1.2.2

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^4.0.0

flutter:
  uses-material-design: true
'''


class ApkBuilder:
    """Packages Forgemind into an Android APK via a Flutter wrapper."""

    def __init__(self, github_token: str = "", repo_name: str = "forgemind-mobile"):
        self.token = github_token
        self.repo_name = repo_name

    def generate_flutter_project(self, output_dir: str = "forgemind-mobile") -> str:
        """Generate a complete Flutter project that wraps Forgemind."""
        root = Path(output_dir)

        # Create directory structure
        dirs = [
            "lib",
            "android/app/src/main/kotlin/com/forgemind",
            "android/app/src/main/res/values",
            ".github/workflows",
        ]
        for d in dirs:
            (root / d).mkdir(parents=True, exist_ok=True)

        # lib/main.dart
        (root / "lib" / "main.dart").write_text(FLUTTER_MAIN)

        # pubspec.yaml
        (root / "pubspec.yaml").write_text(PUBSPEC)

