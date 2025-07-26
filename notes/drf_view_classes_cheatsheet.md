# 🧾 Django REST Framework View Classes Cheatsheet

## 🧱 Base Class
```
APIView
```
- Basic class-based view with:
  - `get()`, `post()`, `patch()`, etc.
  - `request.data`, authentication, permissions
  - Full manual control

---

## 🏗️ Enhanced: `GenericAPIView`
```
APIView
│
├── GenericAPIView
│   ├── + CreateModelMixin       → CreateAPIView
│   ├── + ListModelMixin         → ListAPIView
│   ├── + RetrieveModelMixin     → RetrieveAPIView
│   ├── + UpdateModelMixin       → UpdateAPIView
│   ├── + DestroyModelMixin      → DestroyAPIView
│   └── Combined:
│       ├── ListCreateAPIView
│       ├── RetrieveUpdateAPIView
│       ├── RetrieveDestroyAPIView
│       └── RetrieveUpdateDestroyAPIView
```

✅ Adds helpers like:
- `.get_queryset()`
- `.get_serializer()`
- `.get_object()`
- Easy model/serializer integration

---

## 🧩 Mixins Summary

| Mixin Class             | Method(s) it provides     |
|-------------------------|---------------------------|
| `CreateModelMixin`      | `post()`                  |
| `ListModelMixin`        | `get()` (list view)       |
| `RetrieveModelMixin`    | `get()` (detail view)     |
| `UpdateModelMixin`      | `put()`, `patch()`        |
| `DestroyModelMixin`     | `delete()`                |

---

## 🎛️ ViewSets (for Routers)
```
APIView
│
└── ViewSet
    └── ModelViewSet (adds all CRUD mixins)
```

✅ Use with DRF routers  
✅ Automatically maps `GET`, `POST`, `PATCH`, `DELETE` to endpoints  
✅ Best for full REST API in one class

---

## ✅ When to Use What

| Scenario                                 | View Class              |
|------------------------------------------|--------------------------|
| Full manual logic/control                | `APIView`               |
| Read/update/delete one model instance    | `Retrieve/UpdateAPIView` |
| Read + Create in one endpoint            | `ListCreateAPIView`     |
| All CRUD in one place                    | `ModelViewSet`          |
| You want to work with a router           | `ViewSet` / `ModelViewSet` |
| Only `GET` for many items                | `ListAPIView`           |
| Only `GET` for single item               | `RetrieveAPIView`       |
