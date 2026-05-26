/*
 * MuluOS bundle KIO worker — SCAFFOLD ONLY.
 *
 * The goal of this worker is to make `.exe` bundles appear as a single
 * opaque item in Dolphin (like a macOS .app bundle). Two implementation
 * strategies are possible; this scaffold targets (B):
 *
 *   (A) Custom URL scheme `bundle://`. The worker enumerates installed
 *       bundles and "opens" them by handing off to launch-bundle. Users
 *       navigate to bundle:/ to see their installed apps. Does not change
 *       how file:// browsing of a .exe directory behaves.
 *
 *   (B) Wrap file:// for application/x-muluos-bundle items. The worker is
 *       registered as the handler for that MIME type. When KIO asks for
 *       a UDSEntry for a .exe directory we report it as a regular file
 *       (no S_IFDIR), so Dolphin shows one icon and double-click invokes
 *       the .desktop launcher instead of descending into the directory.
 *       Truly opaque presentation, but more invasive — also has to wire
 *       up `Show Bundle Contents` to fall back to the real file: path.
 *
 * What's stubbed below is the class skeleton + factory; the actual
 * stat()/listDir()/get()/mimetype() bodies are placeholders. Real work
 * to do before this is useful:
 *   - Implement stat(): for a `.exe` path, return UDSEntry with
 *     S_IFREG (so Dolphin treats it as file) and mime
 *     application/x-muluos-bundle.
 *   - Implement listDir(): for the parent dir, list children but
 *     present .exe entries with the masked stat.
 *   - Implement get(): not really meaningful for a bundle; can return
 *     ERR_UNSUPPORTED_ACTION.
 *   - Implement mimetype(): same logic as stat() for the MIME.
 *   - Decide how to expose "Show Bundle Contents": either a separate
 *     `bundle-contents://` scheme or relying on the existing servicemenu
 *     that calls `dolphin <path>` (which bypasses this worker).
 */

#include "muluosbundleworker.h"

#include <QCoreApplication>
#include <QLoggingCategory>

Q_LOGGING_CATEGORY(MULUOS_BUNDLE, "kf.kio.workers.muluosbundle")

extern "C" {
    Q_DECL_EXPORT int kdemain(int argc, char **argv);
}

int kdemain(int argc, char **argv)
{
    QCoreApplication app(argc, argv);
    app.setApplicationName(QStringLiteral("kio_muluosbundle"));

    if (argc != 4) {
        qCCritical(MULUOS_BUNDLE) << "expected pool, app, protocol args";
        return -1;
    }

    MuluOSBundleWorker worker(argv[2], argv[3]);
    worker.dispatchLoop();
    return 0;
}

MuluOSBundleWorker::MuluOSBundleWorker(const QByteArray &pool, const QByteArray &app)
    : KIO::WorkerBase("muluosbundle", pool, app)
{
}

MuluOSBundleWorker::~MuluOSBundleWorker() = default;

KIO::WorkerResult MuluOSBundleWorker::stat(const QUrl &url)
{
    Q_UNUSED(url);
    // TODO: build UDSEntry that reports the .exe as a regular file with
    // MIME application/x-muluos-bundle.
    return KIO::WorkerResult::fail(KIO::ERR_UNSUPPORTED_ACTION,
                                   QStringLiteral("stat not yet implemented"));
}

KIO::WorkerResult MuluOSBundleWorker::listDir(const QUrl &url)
{
    Q_UNUSED(url);
    // TODO: enumerate underlying directory, mask .exe entries.
    return KIO::WorkerResult::fail(KIO::ERR_UNSUPPORTED_ACTION,
                                   QStringLiteral("listDir not yet implemented"));
}

KIO::WorkerResult MuluOSBundleWorker::get(const QUrl &url)
{
    Q_UNUSED(url);
    return KIO::WorkerResult::fail(KIO::ERR_UNSUPPORTED_ACTION,
                                   QStringLiteral("get not supported for bundles"));
}

KIO::WorkerResult MuluOSBundleWorker::mimetype(const QUrl &url)
{
    Q_UNUSED(url);
    // TODO: return application/x-muluos-bundle for .exe paths.
    return KIO::WorkerResult::fail(KIO::ERR_UNSUPPORTED_ACTION,
                                   QStringLiteral("mimetype not yet implemented"));
}
