<template>
  <div class="max-w-3xl mx-auto space-y-8">
    <h1 class="text-2xl font-bold text-gray-900">About This System</h1>

    <!-- Overview -->
    <section>
      <h2 class="text-lg font-semibold text-gray-800 mb-3">Overview</h2>
      <p class="text-gray-600 leading-relaxed">
        PhishGuard is a web-based phishing URL detection system powered by explainable machine learning.
        It analyzes URL structure to identify potential phishing websites and provides transparent,
        SHAP-based explanations for every prediction — so users understand <em>why</em> a URL is flagged,
        not just <em>that</em> it was flagged.
      </p>
    </section>

    <!-- How it works -->
    <section>
      <h2 class="text-lg font-semibold text-gray-800 mb-3">How It Works</h2>
      <div class="grid grid-cols-3 gap-4 text-center">
        <div class="bg-white rounded-xl border p-4">
          <div class="w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-2 text-lg font-bold">1</div>
          <p class="text-sm font-medium text-gray-700">Input</p>
          <p class="text-xs text-gray-500 mt-1">User enters a URL</p>
        </div>
        <div class="bg-white rounded-xl border p-4">
          <div class="w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-2 text-lg font-bold">2</div>
          <p class="text-sm font-medium text-gray-700">Analysis</p>
          <p class="text-xs text-gray-500 mt-1">37 features extracted and scored by ML model</p>
        </div>
        <div class="bg-white rounded-xl border p-4">
          <div class="w-10 h-10 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center mx-auto mb-2 text-lg font-bold">3</div>
          <p class="text-sm font-medium text-gray-700">Result</p>
          <p class="text-xs text-gray-500 mt-1">Risk score + explanation displayed</p>
        </div>
      </div>
    </section>

    <!-- Methodology -->
    <section>
      <h2 class="text-lg font-semibold text-gray-800 mb-3">Methodology</h2>
      <ul class="space-y-2 text-sm text-gray-600">
        <li class="flex items-start gap-2"><span class="text-blue-500 mt-0.5">•</span> Multi-source training data: PhiUSIIL + PhishTank + Tranco</li>
        <li class="flex items-start gap-2"><span class="text-blue-500 mt-0.5">•</span> LightGBM model with Optuna hyperparameter tuning</li>
        <li class="flex items-start gap-2"><span class="text-blue-500 mt-0.5">•</span> Isotonic probability calibration for reliable risk scores</li>
        <li class="flex items-start gap-2"><span class="text-blue-500 mt-0.5">•</span> SHAP TreeExplainer for transparent, per-prediction explanations</li>
        <li class="flex items-start gap-2"><span class="text-blue-500 mt-0.5">•</span> Smart infrastructure-aware data splitting to prevent leakage</li>
      </ul>
    </section>

    <!-- Disclaimers -->
    <section class="bg-amber-50 border-l-4 border-amber-400 rounded-r-xl p-5 space-y-3">
      <h2 class="text-lg font-semibold text-amber-800">Important Disclaimers</h2>
      <div class="space-y-3 text-sm text-amber-900">
        <div>
          <p class="font-medium">Risk Scores</p>
          <p>Risk scores represent calibrated model outputs and should be interpreted as
            decision-support signals, not absolute guarantees. Model accuracy varies with URL types
            and evolving phishing techniques.</p>
        </div>
        <div>
          <p class="font-medium">Known Limitations</p>
          <p>The model analyzes URL structure only. It cannot detect phishing hosted on
            compromised legitimate websites with clean URL patterns. For comprehensive protection,
            combine with content analysis, WHOIS lookup, and threat intelligence feeds.</p>
        </div>
      </div>
    </section>

    <!-- Privacy -->
    <section class="bg-blue-50 border-l-4 border-blue-400 rounded-r-xl p-5 space-y-2">
      <h2 class="text-lg font-semibold text-blue-800">Privacy</h2>
      <ul class="text-sm text-blue-900 space-y-1">
        <li>• Scan history is stored locally in your browser (localStorage)</li>
        <li>• It is never sent to or persisted by the server beyond the inference request</li>
        <li>• The application-level prediction logger does not persist user IP addresses</li>
        <li>• You can clear your history anytime from the Scan page</li>
      </ul>
    </section>

    <!-- Project -->
    <section class="text-center text-sm text-gray-400 pb-4">
      <p>Graduation Project</p>
      <p class="mt-1">Built with FastAPI · Vue 3 · LightGBM · SHAP</p>
    </section>
  </div>
</template>
