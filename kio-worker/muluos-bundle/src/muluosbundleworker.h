#pragma once

#include <KIO/WorkerBase>
#include <QObject>

class MuluOSBundleWorker : public KIO::WorkerBase
{
public:
    MuluOSBundleWorker(const QByteArray &pool, const QByteArray &app);
    ~MuluOSBundleWorker() override;

    // KIO::WorkerBase entry points. Each returns KIO::WorkerResult to
    // signal success/failure. Override as you implement features.
    KIO::WorkerResult stat(const QUrl &url) override;
    KIO::WorkerResult listDir(const QUrl &url) override;
    KIO::WorkerResult get(const QUrl &url) override;
    KIO::WorkerResult mimetype(const QUrl &url) override;
};
