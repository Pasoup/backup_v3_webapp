import CameraSection from "../components/CameraSection";
import ExpectedMedicines from "../components/ExpectedMedicines";
import HowToUse from "../components/HowToUse";

export default function ScanPage({
  expected, setExpected,
  scanResults, setScanResults,
  summary, setSummary,
  annotatedImg,
  isScanning, setIsScanning,
  onScanComplete,
  onComplete,
  resetSession,
}) {
  return (
    <div className=" p-6 flex flex-col gap-5">

      {/* Page header */}
      <div>
        <h1 className="text-xl font-bold text-slate-800">Scan Medicines</h1>
        <p className="text-sm text-slate-500 mt-0.5">
          Place medicine boxes in front of the cameras and press Scan (F4)
        </p>
      </div>

      {/* Expected Medicines — top */}
      <ExpectedMedicines
        expected={expected}
        setExpected={setExpected}
        scanResults={scanResults}
        summary={summary}
        onListChanged={() => {
          setScanResults(null);
          setSummary({ matched: 0, missing: 0, extra: 0, review: 0, unknown: 0 });
          resetSession();
        }}
      />
      {/* Camera Feed — below */}
      <CameraSection
        expected={expected}
        scanResults={scanResults}
        annotatedImg={annotatedImg}
        isScanning={isScanning}
        setIsScanning={setIsScanning}
        onScanComplete={onScanComplete}
        summary={summary}
      />

      {/* Complete button */}
      {(expected.length > 0 || (scanResults && scanResults.length > 0)) && (
        <div className="flex justify-center">
          <button
            onClick={onComplete}
            disabled={isScanning}
            className="flex items-center gap-2 bg-green-600 hover:bg-green-700
                       disabled:bg-slate-300 text-white font-semibold px-8 py-3
                       rounded-2xl shadow-sm hover:shadow-md transition-all text-sm"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            Complete &amp; Save to History
            <span className="text-xs font-mono bg-white/20 px-1.5 py-0.5 rounded">F5</span>
          </button>
        </div>
      )}

      {/* How to use — bottom */}
      <HowToUse />

    </div>
  );
}
