import React from "react";
import { X, Download } from "lucide-react";
import { AnimatePresence, motion } from "framer-motion";

interface PDFViewerOverlayProps {
    pdfUrl: string;
    onClose: () => void;
    isOpen: boolean;
}

export function PDFViewerOverlay({
    pdfUrl,
    onClose,
    isOpen,
}: PDFViewerOverlayProps) {
    const handleDownload = () => {
        const link = document.createElement("a");
        link.href = pdfUrl;
        link.download = "hydrosens-report.pdf";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.3 }}
                        className="fixed inset-0 bg-black/50 z-40"
                        onClick={onClose}
                    />

                    {/* Modal */}
                    <motion.div
                        initial={{ opacity: 0, scale: 0.9 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.9 }}
                        transition={{ type: "tween", duration: 0.3 }}
                        className="fixed top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-50 p-4"
                    >
                        <div className="bg-white rounded-lg shadow-2xl w-[90vw] max-w-6xl h-[100vh] flex flex-col">
                            {/* Header */}
                            <div className="flex items-center justify-between p-4 border-b bg-gray-50 rounded-t-lg">
                                <div className="flex items-center space-x-3">
                                    <div className="w-10 h-10 bg-blue-600 rounded flex items-center justify-center">
                                        <div className="flex flex-col text-white text-xs font-bold leading-none">
                                            <span>RSS</span>
                                        </div>
                                    </div>
                                    <div>
                                        <h2 className="text-lg font-semibold text-gray-800">
                                            RSS HYDROSENS
                                        </h2>
                                        <p className="text-sm text-gray-600">
                                            Environmental Monitoring Report
                                        </p>
                                    </div>
                                </div>
                                <div className="flex items-center space-x-2">
                                    <button
                                        onClick={handleDownload}
                                        className="flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-full hover:bg-blue-700 transition-colors font-medium"
                                    >
                                        <Download className="w-4 h-4" />
                                        Download
                                    </button>
                                    <button
                                        onClick={onClose}
                                        className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
                                    >
                                        <X className="w-5 h-5" />
                                    </button>
                                </div>
                            </div>

                            {/* PDF Viewer */}
                            <div className="flex-1 p-4 bg-gray-100 overflow-hidden">
                                <div className="w-full h-full bg-white rounded shadow-inner">
                                    <iframe
                                        src={`${pdfUrl}#toolbar=0&navpanes=0&scrollbar=0`}
                                        className="w-full h-full rounded border-0"
                                        title="PDF Report"
                                    />
                                </div>
                            </div>

                            {/* Footer */}
                            <div className="p-4 border-t bg-gray-50 rounded-b-lg">
                                <div className="flex items-center justify-end text-sm text-gray-600">
                                    <button
                                        onClick={onClose}
                                        className="px-4 py-2 border border-gray-300 rounded hover:bg-gray-100 transition-colors"
                                    >
                                        Close
                                    </button>
                                </div>
                            </div>
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
